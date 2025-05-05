import pygame
import sys
import random
import time
from math import sqrt
from collections import defaultdict

# 初始化Pygame
pygame.init()

# 游戏常量
WINDOW_SIZE = 800  # 窗口大小
BOARD_SIZE = 15    # 棋盘大小 15x15
GRID_SIZE = 40     # 每个格子大小
PIECE_SIZE = 18    # 棋子大小
SEARCH_DEPTH = 4  # 增加搜索深度
SEARCH_RANGE = 4  # 扩大搜索范围

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BOARD_COLOR = (222, 184, 135)
GRID_COLOR = (0, 0, 0)

# 创建游戏窗口
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption('Five in a Row')

# 初始化棋盘
board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
current_player = 'black'  # 黑子先手

# AI思考时间
thinking_start_time = 0

# 历史启发表
history_table = defaultdict(int)

# 优化评分系统
SCORES = {
    'five': 100000,        # 连五
    'live_four': 10000,    # 活四
    'double_three': 5000,  # 双活三
    'sleep_four': 1000,    # 冲四
    'live_three': 500,     # 活三
    'sleep_three': 200,    # 眠三
    'live_two': 100,      # 活二
    'sleep_two': 50       # 眠二
}

# 方向
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]

# 置换表
transposition_table = {}

# 增加全局变量来记录历史局面
HISTORY_POSITIONS = set()

# 增加开局库
OPENING_MOVES = [
    [(7, 7)],  # 天元
    [(3, 3)],  # 小角
    [(3, 11)], # 小角
    [(11, 3)], # 小角
    [(11, 11)] # 小角
]

def evaluate_pattern(pattern):
    """优化棋型评估"""
    # 必胜棋型
    if '11111' in pattern:
        return 'five'
    if '011110' in pattern:
        return 'live_four'
    
    # 双活三检查
    if pattern.count('01110') >= 2:
        return 'double_three'
        
    # 单个棋型
    if '011110' in pattern:
        return 'live_four'
    if '01111' in pattern or '11110' in pattern:
        return 'sleep_four'
    if '01110' in pattern:
        return 'live_three'
    if '11100' in pattern or '00111' in pattern:
        return 'sleep_three'
    if '01100' in pattern or '00110' in pattern:
        return 'live_two'
    if '11000' in pattern or '00011' in pattern:
        return 'sleep_two'
    
    return None

def get_line_pattern(row, col, dx, dy, color):
    """获取某个方向的棋型"""
    pattern = []
    x, y = row - dx * 4, col - dy * 4
    
    for _ in range(9):  # 检查9个位置以覆盖所有可能的五子连线
        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            if board[x][y] == color:
                pattern.append('1')
            elif board[x][y] is None:
                pattern.append('0')
            else:
                pattern.append('2')
        else:
            pattern.append('2')
        x += dx
        y += dy
    
    return ''.join(pattern)

def check_double_three(row, col, color):
    """检查是否形成双活三"""
    count_live_three = 0
    board[row][col] = color
    
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '01110' in pattern:
            count_live_three += 1
            if count_live_three >= 2:
                board[row][col] = None
                return True
    
    board[row][col] = None
    return False

def check_double_two(row, col, color):
    """检查是否形成双活二"""
    count_live_two = 0
    board[row][col] = color
    
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '01100' in pattern or '00110' in pattern:
            count_live_two += 1
            if count_live_two >= 2:
                board[row][col] = None
                return True
    
    board[row][col] = None
    return False

def get_board_hash():
    """获取当前棋盘状态的哈希值"""
    hash_str = ''.join('0' if x is None else '1' if x == 'black' else '2' for row in board for x in row)
    return hash_str

def evaluate_continuous_threat(row, col, color):
    """评估连续威胁"""
    score = 0
    board[row][col] = color
    
    # 检查是否能在下一步形成威胁
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '011110' in pattern:  # 活四
            score += SCORES['live_four'] * 0.5
        elif '01110' in pattern:  # 活三
            score += SCORES['live_three'] * 0.3
    
    board[row][col] = None
    return score

def check_straight_line(row, col, color):
    """检查是否有直线连子威胁"""
    directions = [(1, 0), (0, 1)]  # 只检查横向和竖向
    board[row][col] = color
    
    for dx, dy in directions:
        count = 1
        # 正向检查
        x, y = row + dx, col + dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x += dx
            y += dy
        
        # 反向检查
        x, y = row - dx, col - dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x -= dx
            y -= dy
            
        if count >= 3:  # 发现三连或更多
            board[row][col] = None
            return True
            
    board[row][col] = None
    return False

def check_diagonal_line(row, col, color):
    """检查斜线连子威胁"""
    directions = [(1, 1), (1, -1)]  # 只检查两个斜向
    board[row][col] = color
    
    for dx, dy in directions:
        count = 1
        # 正向检查
        x, y = row + dx, col + dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x += dx
            y += dy
        
        # 反向检查
        x, y = row - dx, col - dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x -= dx
            y -= dy
            
        if count >= 3:  # 发现三连或更多
            board[row][col] = None
            return True
            
    board[row][col] = None
    return False

def evaluate_position(row, col, color):
    """优化位置评估，增加策略性"""
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE) or board[row][col] is not None:
        return 0
        
    score = 0
    opponent = 'black' if color == 'white' else 'white'
    
    # 进攻评估
    board[row][col] = color
    attack_score = 0
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        pattern_score = evaluate_pattern(pattern)
        if pattern_score:
            attack_score += SCORES[pattern_score]
            # 奖励连续进攻
            if '111' in pattern:
                attack_score *= 1.5
                
    # 防守评估
    board[row][col] = opponent
    defense_score = 0
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, opponent)
        pattern_score = evaluate_pattern(pattern)
        if pattern_score:
            defense_score += SCORES[pattern_score]
    
    # 动态位置价值评估
    center = BOARD_SIZE // 2
    distance_to_center = sqrt((row - center) ** 2 + (col - center) ** 2)
    position_value = 150 * (1 - distance_to_center / (center * sqrt(2)))
    
    # 根据局势动态调整权重
    piece_count = sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] is not None)
    if piece_count < BOARD_SIZE * 2:  # 开局更注重位置和灵活性
        position_weight = random.uniform(1.3, 1.7)
        attack_weight = random.uniform(0.8, 1.2)
        defense_weight = random.uniform(0.8, 1.2)
    else:  # 中后期更注重进攻和防守
        position_weight = random.uniform(0.6, 0.9)
        attack_weight = random.uniform(1.2, 1.5)
        defense_weight = random.uniform(1.1, 1.4)
    
    # 计算最终分数
    board[row][col] = None
    final_score = (attack_score * attack_weight + 
                  defense_score * defense_weight + 
                  position_value * position_weight)
    
    # 增加策略考量
    if check_continuous_threat(row, col, color):
        final_score *= random.uniform(1.2, 1.4)
    if check_offensive_pattern(row, col, color):
        final_score *= random.uniform(1.1, 1.3)
    if check_flexibility(row, col, color):
        final_score *= random.uniform(1.1, 1.2)
        
    return final_score

def evaluate_position_value(row, col, color):
    """评估位置的基础价值"""
    score = 0
    center = BOARD_SIZE // 2
    
    # 中心区域权重
    center_weight = 1.5 - (abs(row - center) + abs(col - center)) / (BOARD_SIZE * 2)
    score += 100 * center_weight
    
    # 检查是否在边缘
    if row == 0 or row == BOARD_SIZE-1 or col == 0 or col == BOARD_SIZE-1:
        score -= 50  # 降低边缘位置的分数
    
    # 检查是否能形成包围态势
    surround_score = 0
    for dx, dy in DIRECTIONS:
        own_count = 0
        opponent_count = 0
        space_count = 0
        
        for step in range(-4, 5):
            new_row = row + dx * step
            new_col = col + dy * step
            if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE:
                if board[new_row][new_col] == color:
                    own_count += 1
                elif board[new_row][new_col] is None:
                    space_count += 1
                else:
                    opponent_count += 1
        
        # 评估包围价值
        if own_count >= 2 and space_count >= 2:
            surround_score += 200
        if opponent_count >= 2 and space_count >= 2:
            surround_score += 150  # 也要考虑阻止对手的包围
    
    score += surround_score
    return score

def evaluate_strategic_value(row, col, color):
    """增强战略评估"""
    score = 0
    opponent = 'black' if color == 'white' else 'white'
    center = BOARD_SIZE // 2
    
    # 中心控制评估
    distance_to_center = sqrt((row - center) ** 2 + (col - center) ** 2)
    center_score = (BOARD_SIZE - distance_to_center) * 100
    score += center_score
    
    # 局部优势评估
    local_score = 0
    for i in range(-2, 3):
        for j in range(-2, 3):
            new_row, new_col = row + i, col + j
            if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE:
                if board[new_row][new_col] == color:
                    local_score += 200 / (abs(i) + abs(j) + 1)
                elif board[new_row][new_col] == opponent:
                    local_score -= 150 / (abs(i) + abs(j) + 1)
    score += local_score
    
    # 防守性评估
    defense_score = 0
    for dx, dy in DIRECTIONS:
        for step in [-1, 1]:
            x, y = row + dx * step, col + dy * step
            if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
                if board[x][y] == opponent:
                    defense_score += 300
    score += defense_score
    
    return score

def evaluate_offensive_value(row, col, color):
    """评估进攻价值"""
    score = 0
    board[row][col] = color
    
    # 检查是否能形成活二
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '01100' in pattern or '00110' in pattern:
            score += SCORES['live_two']
    
    # 检查一子多通
    live_two_count = 0
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '01100' in pattern or '00110' in pattern:
            live_two_count += 1
    if live_two_count >= 2:
        score *= 2  # 一子多通加倍分数
    
    board[row][col] = None
    return score

def evaluate_defensive_value(row, col, opponent_color):
    """增强防守评估"""
    score = 0
    board[row][col] = opponent_color
    
    # 检查四个方向的威胁
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, opponent_color)
        
        # 必须防守的情况
        if '11111' in pattern:  # 连五
            score += SCORES['five'] * 2
        elif '011110' in pattern:  # 活四
            score += SCORES['live_four'] * 2
        elif '11110' in pattern or '01111' in pattern:  # 冲四
            score += SCORES['sleep_four'] * 1.5
        elif '01110' in pattern:  # 活三
            score += SCORES['live_three'] * 1.5
        elif pattern.count('111') >= 1:  # 连续三子
            score += SCORES['live_three']
        
        # 检查潜在威胁
        if '11100' in pattern or '00111' in pattern:  # 眠三
            score += SCORES['sleep_three'] * 1.2
        if '01100' in pattern or '00110' in pattern:  # 活二
            score += SCORES['live_two'] * 1.2
    
    # 检查多重威胁
    threat_count = 0
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, opponent_color)
        if ('11110' in pattern or '01111' in pattern or  # 冲四
            '01110' in pattern):  # 活三
            threat_count += 1
    
    if threat_count >= 2:  # 多重威胁
        score *= 3
    
    board[row][col] = None
    return score

def get_valid_moves():
    """获取有效的落子位置"""
    valid_moves = []
    has_pieces = False
    
    # 遍历棋盘找到所有已有棋子
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] is not None:
                has_pieces = True
                # 搜索周围2格的空位
                for i in range(-2, 3):
                    for j in range(-2, 3):
                        new_row, new_col = row + i, col + j
                        if (0 <= new_row < BOARD_SIZE and 
                            0 <= new_col < BOARD_SIZE and 
                            board[new_row][new_col] is None and
                            (new_row, new_col) not in valid_moves):
                            valid_moves.append((new_row, new_col))
    
    # 如果棋盘为空，返回中心点
    if not has_pieces:
        center = BOARD_SIZE // 2
        return [(center, center)]
    
    return valid_moves

def has_neighbor(row, col):
    """检查是否有相邻的棋子"""
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            new_row, new_col = row + i, col + j
            if (0 <= new_row < BOARD_SIZE and 
                0 <= new_col < BOARD_SIZE and 
                board[new_row][new_col] is not None):
                return True
    return False

def iterative_deepening_search(max_depth):
    """迭代加深搜索"""
    best_move = None
    best_score = float('-inf')
    
    for depth in range(2, max_depth + 1):
        score, move = minimax(depth, float('-inf'), float('inf'), True)
        if move:
            best_move = move
            best_score = score
    
    return best_move

def minimax(depth, alpha, beta, is_maximizing, move=None):
    """极大极小算法带Alpha-Beta剪枝"""
    if depth == 0:
        return evaluate_position(move[0], move[1], 'white' if is_maximizing else 'black'), move
    
    valid_moves = get_valid_moves()
    best_move = None
    
    if is_maximizing:
        max_eval = float('-inf')
        for row, col in valid_moves:
            if board[row][col] is None and has_neighbor(row, col):
                board[row][col] = 'white'
                eval, _ = minimax(depth - 1, alpha, beta, False, (row, col))
                board[row][col] = None
                
                if eval > max_eval:
                    max_eval = eval
                    best_move = (row, col)
                
                alpha = max(alpha, eval)
                if beta <= alpha:
                    history_table[(row, col)] += depth * depth
                    break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for row, col in valid_moves:
            if board[row][col] is None and has_neighbor(row, col):
                board[row][col] = 'black'
                eval, _ = minimax(depth - 1, alpha, beta, True, (row, col))
                board[row][col] = None
                
                if eval < min_eval:
                    min_eval = eval
                    best_move = (row, col)
                
                beta = min(beta, eval)
                if beta <= alpha:
                    history_table[(row, col)] += depth * depth
                    break
        return min_eval, best_move

def check_draw():
    """检查是否平局"""
    # 检查是否还有空位
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] is None:
                return False
    return True

def get_ai_move():
    """优化AI决策，增加策略性和变化性"""
    valid_moves = get_valid_moves()
    if not valid_moves:
        return None
        
    # 检查开局阶段
    piece_count = sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] is not None)
    
    # 开局阶段使用开局库
    if piece_count < 6:
        # 第一手
        if piece_count == 0:
            return random.choice(OPENING_MOVES)[0]
        # 后续开局
        elif piece_count < 6:
            # 有30%概率下随机位置（增加变化）
            if random.random() < 0.3:
                center = BOARD_SIZE // 2
                radius = random.randint(2, 4)
                candidates = []
                for row in range(max(0, center-radius), min(BOARD_SIZE, center+radius+1)):
                    for col in range(max(0, center-radius), min(BOARD_SIZE, center+radius+1)):
                        if board[row][col] is None and has_neighbor(row, col):
                            candidates.append((row, col))
                if candidates:
                    return random.choice(candidates)
    
    # 检查必胜和必防
    for row, col in valid_moves:
        # 检查我方能否获胜
        board[row][col] = current_player
        if check_win(row, col):
            board[row][col] = None
            return row, col
            
        # 检查对手能否获胜
        opponent = 'black' if current_player == 'white' else 'white'
        board[row][col] = opponent
        if check_win(row, col):
            board[row][col] = None
            return row, col
            
        board[row][col] = None
    
    # 动态调整搜索深度和策略
    if piece_count < 20:  # 开局阶段
        depth = random.choice([2, 3])  # 随机深度
        strategy = 'position'  # 注重位置
    elif piece_count < 40:  # 中局
        depth = random.choice([3, 4])  # 随机深度
        strategy = 'attack' if random.random() < 0.6 else 'defense'  # 偏向进攻
    else:  # 残局
        depth = 4
        strategy = 'win'  # 全力争胜
    
    # 根据不同策略评估局面
    best_moves = []
    best_score = float('-inf')
    
    for row, col in valid_moves:
        # 基础分数
        score = evaluate_position(row, col, current_player)
        
        # 根据策略调整分数
        if strategy == 'position':
            # 更注重位置价值和灵活性
            center = BOARD_SIZE // 2
            dist_to_center = sqrt((row - center) ** 2 + (col - center) ** 2)
            position_bonus = 200 * (1 - dist_to_center / (center * sqrt(2)))
            score = score * 0.7 + position_bonus
            
            # 奖励灵活性
            if check_flexibility(row, col, current_player):
                score *= 1.3
                
        elif strategy == 'attack':
            # 更注重进攻和连续威胁
            if check_offensive_pattern(row, col, current_player):
                score *= 1.5
            if check_continuous_threat(row, col, current_player):
                score *= 1.4
                
        elif strategy == 'defense':
            # 更注重防守和阻止对手
            opponent = 'black' if current_player == 'white' else 'white'
            if check_offensive_pattern(row, col, opponent):
                score *= 1.6
            if check_critical_threat(row, col, opponent):
                score *= 1.5
                
        # 增加随机波动
        score *= random.uniform(0.8, 1.2)
        
        # 收集最佳移动
        if score > best_score:
            best_score = score
            best_moves = [(row, col)]
        elif abs(score - best_score) < 200:  # 允许更多次优解
            best_moves.append((row, col))
    
    # 使用加权随机选择
    if best_moves:
        weights = []
        for r, c in best_moves:
            # 基础权重
            weight = 1.0
            # 根据位置调整权重
            center = BOARD_SIZE // 2
            dist = sqrt((r - center) ** 2 + (c - center) ** 2)
            weight *= (1 + 0.5 * (1 - dist / (center * sqrt(2))))
            # 根据威胁程度调整权重
            if check_critical_threat(r, c, current_player):
                weight *= 1.3
            weights.append(weight)
            
        return random.choices(best_moves, weights=weights)[0]
    
    return valid_moves[0]

def check_critical_threat(row, col, color):
    """检查是否有关键威胁（活四或双活三）"""
    board[row][col] = color
    has_threat = False
    
    # 检查活四
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '011110' in pattern:  # 活四
            has_threat = True
            break
    
    # 检查双活三
    if not has_threat:
        three_count = 0
        for dx, dy in DIRECTIONS:
            pattern = get_line_pattern(row, col, dx, dy, color)
            if '01110' in pattern:  # 活三
                three_count += 1
                if three_count >= 2:
                    has_threat = True
                    break
    
    board[row][col] = None
    return has_threat

def evaluate_complex_pattern(row, col, color):
    """评估复杂棋型组合"""
    score = 0
    board[row][col] = color
    
    # 检查四个方向
    patterns = []
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        patterns.append(pattern)
    
    # 检查复杂棋型组合
    four_count = 0  # 四的数量
    three_count = 0  # 活三数量
    sleep_three_count = 0  # 眠三数量
    two_count = 0  # 活二数量
    
    for pattern in patterns:
        # 检查活四
        if '011110' in pattern:
            score += SCORES['live_four']
            four_count += 1
        # 检查冲四
        elif '01111' in pattern or '11110' in pattern:
            score += SCORES['sleep_four']
            four_count += 1
        # 检查活三
        elif '01110' in pattern:
            score += SCORES['live_three']
            three_count += 1
        # 检查眠三
        elif '11100' in pattern or '00111' in pattern:
            score += SCORES['sleep_three']
            sleep_three_count += 1
        # 检查活二
        elif '01100' in pattern or '00110' in pattern:
            score += SCORES['live_two']
            two_count += 1
    
    # 评估组合棋型
    if four_count >= 2:
        score += SCORES['double_four']
    if three_count >= 2:
        score += SCORES['double_three']
    if two_count >= 2:
        score += SCORES['double_two']
    
    # 检查潜在威胁
    for pattern in patterns:
        if '010110' in pattern or '011010' in pattern:  # 潜在活四
            score += SCORES['live_three']
        if '001110' in pattern or '011100' in pattern:  # 潜在活三
            score += SCORES['potential_three']
    
    board[row][col] = None
    return score

def draw_board():
    """绘制棋盘"""
    # 填充棋盘背景色
    screen.fill(BOARD_COLOR)
    
    # 计算偏移量使棋盘居中
    offset = (WINDOW_SIZE - (BOARD_SIZE - 1) * GRID_SIZE) // 2
    
    # 绘制网格线
    for i in range(BOARD_SIZE):
        # 横线
        pygame.draw.line(screen, GRID_COLOR,
                        (offset, offset + i * GRID_SIZE),
                        (WINDOW_SIZE - offset, offset + i * GRID_SIZE))
        # 竖线
        pygame.draw.line(screen, GRID_COLOR,
                        (offset + i * GRID_SIZE, offset),
                        (offset + i * GRID_SIZE, WINDOW_SIZE - offset))

def draw_pieces():
    """绘制棋子"""
    offset = (WINDOW_SIZE - (BOARD_SIZE - 1) * GRID_SIZE) // 2
    
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col]:
                color = BLACK if board[row][col] == 'black' else WHITE
                center = (offset + col * GRID_SIZE, offset + row * GRID_SIZE)
                pygame.draw.circle(screen, color, center, PIECE_SIZE)
                # 为白子添加黑色边框
                if board[row][col] == 'white':
                    pygame.draw.circle(screen, BLACK, center, PIECE_SIZE, 1)

def get_grid_position(pos):
    """将鼠标位置转换为棋盘格子位置"""
    offset = (WINDOW_SIZE - (BOARD_SIZE - 1) * GRID_SIZE) // 2
    x, y = pos
    
    # 计算最近的交叉点
    col = round((x - offset) / GRID_SIZE)
    row = round((y - offset) / GRID_SIZE)
    
    # 确保在棋盘范围内
    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
        return row, col
    return None

def check_win(row, col):
    """检查是否获胜"""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 横、竖、右斜、左斜
    color = board[row][col]
    
    for dx, dy in directions:
        count = 1  # 当前位置已经有一个棋子
        
        # 正向检查
        x, y = row + dx, col + dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x += dx
            y += dy
        
        # 反向检查
        x, y = row - dx, col - dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x -= dx
            y -= dy
        
        if count >= 5:
            return True
    return False

def evaluate_opening_stage():
    """评估是否处于开局阶段"""
    piece_count = sum(1 for row in board for cell in row if cell is not None)
    return piece_count <= 7  # 7手以内为开局阶段

def get_opening_move():
    """获取开局阶段的落子位置"""
    center = BOARD_SIZE // 2
    piece_count = sum(1 for row in board for cell in row if cell is not None)
    
    # 白棋开局以防守为主
    if piece_count < 4:
        # 优先选择靠近黑子的位置进行防守
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if board[row][col] == 'black':
                    # 在黑子周围2格范围内寻找防守点
                    for i in range(-2, 3):
                        for j in range(-2, 3):
                            new_row, new_col = row + i, col + j
                            if (0 <= new_row < BOARD_SIZE and 
                                0 <= new_col < BOARD_SIZE and 
                                board[new_row][new_col] is None):
                                return new_row, new_col
    
    return None

def check_vcf(row, col, color):
    """检查是否可以实施VCF战术(连续冲四)"""
    board[row][col] = color
    vcf_moves = []
    
    # 检查四个方向
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '11110' in pattern or '01111' in pattern:  # 冲四
            vcf_moves.append((row, col))
            # 寻找下一个冲四点
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if board[r][c] is None:
                        board[r][c] = color
                        next_pattern = get_line_pattern(r, c, dx, dy, color)
                        if '11110' in next_pattern or '01111' in next_pattern:
                            vcf_moves.append((r, c))
                        board[r][c] = None
    
    board[row][col] = None
    return len(vcf_moves) >= 2  # 至少需要两步连续冲四

def check_vct(row, col, color):
    """检查是否可以实施VCT战术(连续活三)"""
    board[row][col] = color
    has_vct = False
    
    # 检查是否形成活三
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '01110' in pattern:  # 活三
            # 寻找下一个活三点
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if board[r][c] is None:
                        board[r][c] = color
                        next_pattern = get_line_pattern(r, c, dx, dy, color)
                        if '01110' in next_pattern:  # 再次形成活三
                            has_vct = True
                        board[r][c] = None
                        if has_vct:
                            break
                if has_vct:
                    break
    
    board[row][col] = None
    return has_vct

def draw_mode_selection():
    """绘制模式选择界面"""
    screen.fill(BOARD_COLOR)
    font = pygame.font.Font(None, 36)
    
    # 显示选项
    text1 = font.render('1: Player vs AI', True, BLACK)
    text2 = font.render('2: AI vs AI', True, BLACK)
    text3 = font.render('3: Player vs Player', True, BLACK)
    
    text1_rect = text1.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 40))
    text2_rect = text2.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
    text3_rect = text3.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 40))
    
    screen.blit(text1, text1_rect)
    screen.blit(text2, text2_rect)
    screen.blit(text3, text3_rect)
    
    pygame.display.flip()
    
    # 等待用户选择
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    # 使用时间作为随机种子
                    random.seed(time.time())
                    # 80%的概率玩家是黑色
                    player_is_black = random.random() < 0.8
                    return ('pvai', player_is_black)
                elif event.key == pygame.K_2:
                    return ('aivai', None)
                elif event.key == pygame.K_3:
                    return ('pvp', None)

def select_game_mode():
    """选择游戏模式"""
    screen.fill(BOARD_COLOR)
    font = pygame.font.Font(None, 36)
    
    # 显示选项
    text1 = font.render('1: Player vs AI', True, BLACK)
    text2 = font.render('2: AI vs AI', True, BLACK)
    text3 = font.render('3: Player vs Player', True, BLACK)
    
    text1_rect = text1.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 40))
    text2_rect = text2.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
    text3_rect = text3.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 40))
    
    screen.blit(text1, text1_rect)
    screen.blit(text2, text2_rect)
    screen.blit(text3, text3_rect)
    
    pygame.display.flip()
    
    # 等待用户选择
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    # 使用时间作为随机种子
                    random.seed(time.time())
                    # 80%的概率玩家是黑色
                    player_is_black = random.random() < 0.8
                    return ('pvai', player_is_black)
                elif event.key == pygame.K_2:
                    return ('aivai', None)
                elif event.key == pygame.K_3:
                    return ('pvp', None)

def check_immediate_threat(row, col, color):
    """检查是否有紧迫威胁（快要连五）"""
    # 检查四个方向
    for dx, dy in DIRECTIONS:
        # 正向检查
        count = 1
        x, y = row + dx, col + dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x += dx
            y += dy
            
        # 反向检查
        x, y = row - dx, col - dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == color:
            count += 1
            x -= dx
            y -= dy
            
        if count >= 4:  # 已经有四个连续棋子
            return True
    return False

def get_candidate_moves(color):
    """优化候选移动生成"""
    moves = []
    opponent = 'black' if color == 'white' else 'white'
    
    # 找出所有已下子的位置
    pieces = []
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] is not None:
                pieces.append((i, j))
    
    # 如果棋盘为空，返回中心点
    if not pieces:
        center = BOARD_SIZE // 2
        return [(center, center)]
    
    # 在已有棋子周围寻找候选点
    candidates = set()
    for row, col in pieces:
        for i in range(-SEARCH_RANGE, SEARCH_RANGE + 1):
            for j in range(-SEARCH_RANGE, SEARCH_RANGE + 1):
                new_row, new_col = row + i, col + j
                if (0 <= new_row < BOARD_SIZE and 
                    0 <= new_col < BOARD_SIZE and 
                    board[new_row][new_col] is None):
                    candidates.add((new_row, new_col))
    
    # 评估每个候选点
    for row, col in candidates:
        score = evaluate_position(row, col, color)
        moves.append((score, row, col))
    
    # 按分数降序排序，只返回前N个最佳候选点
    moves.sort(reverse=True)
    return [(row, col) for _, row, col in moves[:15]]  # 只考虑最佳的15个位置

def check_live_four(row, col, color):
    """检查是否可以形成活四"""
    board[row][col] = color
    has_live_four = False
    
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if '011110' in pattern:  # 活四
            has_live_four = True
            break
    
    board[row][col] = None
    return has_live_four

def check_continuous_threat(row, col, color):
    """检查是否能形成连续威胁"""
    board[row][col] = color
    threat_count = 0
    
    # 检查四个方向
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        # 检查是否形成威胁
        if ('11110' in pattern or '01111' in pattern or  # 冲四
            '01110' in pattern or  # 活三
            pattern.count('111') >= 1):  # 连续三子
            threat_count += 1
    
    board[row][col] = None
    return threat_count >= 2  # 至少有两个方向形成威胁

def check_offensive_pattern(row, col, color):
    """检查是否能形成进攻态势"""
    board[row][col] = color
    has_offensive = False
    
    # 检查是否能形成活三或更强的威胁
    for dx, dy in DIRECTIONS:
        pattern = get_line_pattern(row, col, dx, dy, color)
        if ('01110' in pattern or  # 活三
            '11100' in pattern or '00111' in pattern or  # 眠三
            pattern.count('111') >= 1):  # 连续三子
            has_offensive = True
            break
    
    board[row][col] = None
    return has_offensive

def check_flexibility(row, col, color):
    """检查位置的灵活性"""
    board[row][col] = color
    flexibility = 0
    
    # 检查周围8个方向
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            # 检查该方向是否有发展空间
            r, c = row + dr, col + dc
            if (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and 
                board[r][c] is None):
                flexibility += 1
                
    board[row][col] = None
    return flexibility >= 4  # 至少有4个方向有发展空间

def main():
    """主游戏循环"""
    global current_player, thinking_start_time, HISTORY_POSITIONS, game_mode
    
    # 选择游戏模式
    game_mode, player_is_black = select_game_mode()
    
    game_over = False
    ai_thinking = False
    last_move_time = 0
    draw = False
    
    # 重置历史位置记录
    HISTORY_POSITIONS = set()
    
    while True:
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            # 处理玩家落子
            if (event.type == pygame.MOUSEBUTTONDOWN and 
                not game_over and 
                not draw and
                (game_mode == 'pvp' or 
                 (game_mode == 'pvai' and 
                  ((player_is_black and current_player == 'black') or
                   (not player_is_black and current_player == 'white')))) and
                not ai_thinking and 
                current_time - last_move_time > 0.1):
                
                pos = get_grid_position(event.pos)
                if pos and board[pos[0]][pos[1]] is None:
                    row, col = pos
                    board[row][col] = current_player
                    last_move_time = current_time
                    
                    if check_win(row, col):
                        game_over = True
                    elif check_draw():
                        draw = True
                    else:
                        current_player = 'white' if current_player == 'black' else 'black'
                        if game_mode == 'pvai':
                            ai_thinking = True
                            thinking_start_time = current_time
            
            # 按空格键重新开始游戏
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                board.clear()
                board.extend([[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)])
                game_mode, player_is_black = select_game_mode()
                current_player = 'black'
                game_over = False
                draw = False
                ai_thinking = False
                last_move_time = 0
                
        # 绘制游戏界面
        draw_board()
        draw_pieces()
        
        # AI回合
        if ((game_mode == 'pvai' and 
             ((not player_is_black and current_player == 'black') or
              (player_is_black and current_player == 'white'))) or 
            (game_mode == 'aivai' and not game_over and not draw)) and not game_over:
            
            if current_time - thinking_start_time > 0.6:
                ai_move = get_ai_move()
                if ai_move:
                    row, col = ai_move
                    board[row][col] = current_player
                    last_move_time = current_time
                    
                    if check_win(row, col):
                        game_over = True
                    elif check_draw():
                        draw = True
                    else:
                        current_player = 'black' if current_player == 'white' else 'white'
                        thinking_start_time = current_time
                else:
                    draw = True
                        
                if game_mode == 'pvai':
                    ai_thinking = False
        
        # 显示当前玩家和游戏状态
        font = pygame.font.Font(None, 36)
        if game_over:
            if game_mode == 'pvp':
                winner = 'Black' if current_player == 'black' else 'White'
            elif game_mode == 'pvai':
                if (player_is_black and current_player == 'black') or (not player_is_black and current_player == 'white'):
                    winner = 'You'
                else:
                    winner = 'AI'
            else:
                winner = 'Black AI' if current_player == 'black' else 'White AI'
            text = font.render(f'{winner} Wins! Press SPACE to restart', True, BLACK)
        elif draw:
            text = font.render('Draw! Press SPACE to restart', True, BLACK)
        else:
            if game_mode == 'pvp':
                current = 'Black' if current_player == 'black' else 'White'
            elif game_mode == 'pvai':
                if (player_is_black and current_player == 'black') or (not player_is_black and current_player == 'white'):
                    current = 'Your'
                else:
                    current = "AI's"
            else:
                current = 'Black AI' if current_player == 'black' else 'White AI'
            text = font.render(f'Current Turn: {current}', True, BLACK)
        
        text_rect = text.get_rect(center=(WINDOW_SIZE // 2, 30))
        screen.blit(text, text_rect)
        
        pygame.display.flip()

if __name__ == '__main__':
    main()
