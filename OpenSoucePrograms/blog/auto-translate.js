// 🌐 智能全局翻译系统 - 封装版，避免全局变量重复

(function () {
  console.debug('DEBUG: 初始化翻译系统 - 安全版');

  // 存储语言状态在本地存储中，使其在页面刷新后保持
  let currentLang = localStorage.getItem('butterfly_translate_lang') || 'zh';
  const originalContent = new Map();
  const translatedContent = new Map();
  // 恢复跳过选择器，避免翻译太多内容导致格式问题
  const skipSelectors = [
    'pre', 'code', 'script', 'style', 'iframe', 'canvas', 'svg', 
    '.code-block', '.katex', '.mermaid', '.chartjs', 'iframe',
    'link', 'meta', 'style', 'script', '.highlight', '.copy-button',
    '[class*="language-"]', '.line-numbers', '.has-jax', '.math',
    '.wl-note', '.wl-card', '.copyright-info', '.post-copyright'
  ];
  
  // 限制翻译选择器，只翻译常见的文本元素
  const translateSelectors = [
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'em', 'strong', 
    'td', 'th', 'caption', // 表格相关，但更有限
    'span:not(.icon)', 'a.article-title', 'a.post-title', // 有限的链接和span
    'div.post-title', 'div.article-title', // 标题div
    'blockquote', 'figcaption' // 其他常见文本元素
  ];

  function initTranslation() {
    console.debug('DEBUG: 初始化安全翻译系统 - 仅翻译普通文本内容');
    updateUILanguage();
    
    // 检查是否在文章页面
    if (isArticlePage()) {
      // 创建悬浮翻译按钮
      createFloatingButton();
      
      // 如果当前语言是英文，自动应用翻译
      if (currentLang === 'en') {
        setTimeout(() => {
          console.debug('DEBUG: 自动应用英文翻译');
          translate('en');
        }, 500);
      }
    }
  }
  
  // 检查当前是否在文章页面
  function isArticlePage() {
    // 检查多种可能的文章页面标识
    return Boolean(
      document.getElementById('article-container') || 
      document.querySelector('.post-content') || 
      document.querySelector('article') || 
      document.querySelector('.post') ||
      document.querySelector('.article') ||
      // 检查URL是否包含post或article等标识
      window.location.pathname.includes('/post/') ||
      window.location.pathname.includes('/article/') ||
      window.location.pathname.match(/\/\d{4}\/\d{2}\/\d{2}\//)
    );
  }

  function createFloatingButton() {
    // 检查是否已经存在按钮
    if (document.getElementById('floating-translate-btn')) return;
    
    console.debug('DEBUG: 创建悬浮翻译按钮');
    
    const floatingBtn = document.createElement('div');
    floatingBtn.id = 'floating-translate-btn';
    floatingBtn.innerHTML = currentLang === 'zh' ? '🌐 En' : '🌐 中';
    
    // 添加样式
    Object.assign(floatingBtn.style, {
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      color: 'white',
      padding: '8px 12px',
      borderRadius: '20px',
      fontSize: '14px',
      cursor: 'pointer',
      zIndex: '9999',
      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
      transition: 'all 0.3s ease'
    });
    
    // 悬停效果
    floatingBtn.addEventListener('mouseover', () => {
      floatingBtn.style.backgroundColor = 'rgba(0, 0, 0, 0.85)';
      floatingBtn.style.transform = 'scale(1.05)';
    });
    
    floatingBtn.addEventListener('mouseout', () => {
      floatingBtn.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
      floatingBtn.style.transform = 'scale(1)';
    });
    
    // 点击事件
    floatingBtn.addEventListener('click', async () => {
      console.debug('DEBUG: 翻译按钮被点击');
      const newLang = currentLang === 'zh' ? 'en' : 'zh';
      floatingBtn.innerHTML = '⏳ 翻译中...';
      floatingBtn.style.pointerEvents = 'none';
      floatingBtn.style.opacity = '0.7';
      
      await translate(newLang);
      
      floatingBtn.innerHTML = currentLang === 'zh' ? '🌐 En' : '🌐 中';
      floatingBtn.style.pointerEvents = 'auto';
      floatingBtn.style.opacity = '1';
    });
    
    document.body.appendChild(floatingBtn);
  }

  function updateUILanguage() {
    const items = document.querySelectorAll('.menus_item_child a.site-page.child');
    items.forEach(item => {
      if (item.textContent.includes('中文')) item.innerHTML = '🌐 中文';
      if (item.textContent.includes('English')) item.innerHTML = '🌐 English';
    });
    
    // 更新翻译按钮
    const floatingBtn = document.getElementById('floating-translate-btn');
    if (floatingBtn) {
      floatingBtn.innerHTML = currentLang === 'zh' ? '🌐 En' : '🌐 中';
    }
  }

  function bindDropdownEvents() {
    console.debug('DEBUG: 尝试绑定语言菜单点击事件');

    const items = [...document.querySelectorAll('.menus_item_child a.site-page.child')];
    const zhItem = items.find(i => i.textContent.includes('中文'));
    const enItem = items.find(i => i.textContent.includes('English'));

    console.debug('DEBUG: 找到菜单项:', { zhItem, enItem });

    if (zhItem) {
      zhItem.addEventListener('click', e => {
        e.preventDefault();
        console.debug('DEBUG: 点击了【中文】按钮');
        translate('zh');
      });
    }

    if (enItem) {
      enItem.addEventListener('click', e => {
        e.preventDefault();
        console.debug('DEBUG: 点击了【English】按钮');
        translate('en');
      });
    }
  }

  async function translate(targetLang) {
    if (targetLang === currentLang) {
      console.debug('DEBUG: 当前语言已是目标语言，无需切换');
      return;
    }

    // 仅使用文章相关容器，避免翻译导航、侧边栏等UI元素
    let containers = [];
    
    // 主要内容容器
    const mainContainer = document.getElementById('article-container') || 
                          document.querySelector('.post-content') || 
                          document.querySelector('article') || 
                          document.querySelector('.post') ||
                          document.querySelector('.article');
    
    if (mainContainer) {
      containers.push(mainContainer);
    } else {
      // 如果找不到主容器，使用一个更有限的选择
      const contentArea = document.querySelector('main') || document.querySelector('#content-inner');
      if (contentArea) containers.push(contentArea);
    }
    
    // 添加标题元素
    const titleElement = document.querySelector('.post-title') || document.querySelector('.article-title');
    if (titleElement) containers.push(titleElement);
    
    if (containers.length === 0) {
      console.error('DEBUG: 未找到任何内容容器');
      return;
    }
    
    console.debug(`DEBUG: 找到 ${containers.length} 个内容容器`);

    if (targetLang === 'zh') {
      restoreOriginalContent();
      currentLang = 'zh';
      // 保存当前语言到本地存储
      localStorage.setItem('butterfly_translate_lang', currentLang);
      updateUILanguage();
      return;
    }

    let elements = [];
    // 从每个容器中获取可翻译元素
    containers.forEach(container => {
      elements = [...elements, ...findTranslatableElements(container)];
    });
    
    // 去重
    elements = [...new Set(elements)];
    
    console.debug(`DEBUG: 总共找到 ${elements.length} 个唯一的可翻译元素（安全模式）`);
    
    if (originalContent.size === 0) {
      elements.forEach(el => originalContent.set(el, el.textContent));
    }

    if (translatedContent.size > 0) {
      applyTranslatedContent();
      currentLang = 'en';
      // 保存当前语言到本地存储
      localStorage.setItem('butterfly_translate_lang', currentLang);
      updateUILanguage();
      return;
    }

    // 分批翻译，避免请求过大
    const batchSize = 50;
    console.debug(`DEBUG: 将分成 ${Math.ceil(elements.length / batchSize)} 批进行翻译`);
    
    for (let i = 0; i < elements.length; i += batchSize) {
      const batch = elements.slice(i, i + batchSize);
      const texts = batch.map(el => el.textContent.trim()).filter(Boolean);
      const combined = texts.join('\n[SPLIT]\n');
      
      console.debug(`DEBUG: 正在请求翻译批次 ${Math.floor(i/batchSize) + 1}，内含 ${texts.length} 段内容`);
      
      const result = await translateText(combined, 'zh-CN', 'en');
      if (!result) {
        console.error('DEBUG: 批次翻译结果为空');
        continue;
      }
      
      const translatedTexts = result.split('\n[SPLIT]\n');
      for (let j = 0; j < batch.length; j++) {
        translatedContent.set(batch[j], translatedTexts[j] || '');
        batch[j].textContent = translatedTexts[j] || '';
      }
      
      console.debug(`DEBUG: 批次 ${Math.floor(i/batchSize) + 1} 翻译完成`);
    }

    currentLang = 'en';
    // 保存当前语言到本地存储
    localStorage.setItem('butterfly_translate_lang', currentLang);
    updateUILanguage();
    console.debug('DEBUG: 所有内容翻译完成 ✅');
  }

  function findTranslatableElements(container) {
    const selector = translateSelectors.join(', ');
    const all = container.querySelectorAll(selector);
    const elements = [];
    const processed = new Set();

    all.forEach(el => {
      // 如果元素已处理或没有文本，跳过
      if (processed.has(el) || !el.textContent.trim()) return;
      
      // 检查是否在排除列表中
      let shouldSkip = false;
      let parent = el;
      while (parent && parent !== container) {
        if (skipSelectors.some(sel => {
          try {
            return parent.matches ? parent.matches(sel) : parent.msMatchesSelector && parent.msMatchesSelector(sel);
          } catch (e) {
            return false; // 忽略无效的选择器
          }
        })) {
          shouldSkip = true;
          break;
        }
        parent = parent.parentElement;
      }
      
      if (shouldSkip) return;
      
      // 对于表格元素，特殊处理
      if (el.tagName === 'TABLE') {
        // 表格本身添加到处理列表，以防递归处理时跳过
        processed.add(el);
        
        // 直接处理所有表头和单元格
        const cells = el.querySelectorAll('th, td');
        cells.forEach(cell => {
          if (!processed.has(cell) && cell.textContent.trim() && !shouldSkipElement(cell, container)) {
            elements.push(cell);
            processed.add(cell);
          }
        });
        
        // 处理表格标题
        const caption = el.querySelector('caption');
        if (caption && !processed.has(caption) && caption.textContent.trim() && !shouldSkipElement(caption, container)) {
          elements.push(caption);
          processed.add(caption);
        }
        
        return;
      }
      
      // 对于标题元素，直接处理
      if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(el.tagName) || 
          el.classList.contains('post-title') || 
          el.classList.contains('article-title')) {
        elements.push(el);
        processed.add(el);
        return;
      }
      
      // 智能处理元素内容：避免翻译已包含在其他元素中的子元素
      // 检查是否有子元素也在翻译列表中
      const childTranslatables = Array.from(el.querySelectorAll(selector))
        .filter(child => child.textContent.trim() && !processed.has(child) && !shouldSkipElement(child, container));
      
      // 如果没有可翻译子元素，或者元素纯文本占比很高，则翻译整个元素
      const directTextContent = Array.from(el.childNodes)
        .filter(node => node.nodeType === 3) // 文本节点
        .map(node => node.textContent.trim())
        .join('');
      
      const hasSignificantDirectText = directTextContent.length > 10 || 
                                      (directTextContent.length > 0 && directTextContent.length >= el.textContent.length * 0.5);
      
      if (childTranslatables.length === 0 || hasSignificantDirectText) {
        elements.push(el);
        processed.add(el);
      } else {
        // 否则递归处理子元素
        childTranslatables.forEach(child => {
          if (!processed.has(child) && !shouldSkipElement(child, container)) {
            elements.push(child);
            processed.add(child);
          }
        });
      }
    });

    console.debug(`DEBUG: 在容器中找到 ${elements.length} 个可翻译元素`);
    return elements;
  }
  
  // 辅助函数：检查元素是否应该跳过
  function shouldSkipElement(el, container) {
    let parent = el;
    while (parent && parent !== container) {
      if (skipSelectors.some(sel => {
        try {
          return parent.matches ? parent.matches(sel) : parent.msMatchesSelector && parent.msMatchesSelector(sel);
        } catch (e) {
          return false; // 忽略无效的选择器
        }
      })) {
        return true;
      }
      parent = parent.parentElement;
    }
    return false;
  }

  async function translateText(text, from, to) {
    try {
      console.debug('DEBUG: 调用 Google Translate 接口');
      // 添加延迟，避免请求过于频繁
      await new Promise(resolve => setTimeout(resolve, 300));
      const res = await fetch(`https://translate.googleapis.com/translate_a/single?client=gtx&sl=${from}&tl=${to}&dt=t&q=${encodeURIComponent(text)}`);
      
      if (!res.ok) {
        console.error(`DEBUG: 翻译请求失败，状态码: ${res.status}`);
        return null;
      }
      
      const data = await res.json();
      if (!data || !data[0]) {
        console.error('DEBUG: 解析翻译结果失败');
        return null;
      }
      
      return data[0].map(item => item[0]).join('');
    } catch (e) {
      console.error('DEBUG: 翻译 API 调用失败', e);
      return null;
    }
  }

  function restoreOriginalContent() {
    originalContent.forEach((val, el) => {
      if (el && el.parentNode) el.textContent = val;
    });
    console.debug('DEBUG: 内容已恢复为中文');
  }

  function applyTranslatedContent() {
    translatedContent.forEach((val, el) => {
      if (el && el.parentNode) el.textContent = val;
    });
    console.debug('DEBUG: 已应用缓存翻译内容');
  }

  document.addEventListener('DOMContentLoaded', () => {
    console.debug('DEBUG: DOMContentLoaded 事件触发');
    initTranslation();
    bindDropdownEvents();
  });

  document.addEventListener('pjax:complete', () => {
    console.debug('DEBUG: PJAX 完成事件触发');
    // 清除之前的内容缓存
    originalContent.clear();
    translatedContent.clear();
    // 重新初始化
    initTranslation();
    bindDropdownEvents();
  });
})();