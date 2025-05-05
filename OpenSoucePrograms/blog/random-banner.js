/**
 * 多源随机Banner图片加载器
 * 支持多个图源服务，关键词筛选，失败降级，PJAX兼容
 * 仅用于非文章页面
 * 版本: 2.2.0 (优先使用Picsum，降低Unsplash优先级)
 */

(function() {
  console.log("===== 随机Banner加载器2.1初始化 =====");
  
  // 确保在DOM加载完成后执行
  function init() {
    // 强制检测页面类型
    const isPostPage = document.body && (
                      document.body.classList.contains('post') || 
                      document.querySelector('body.post-template') || 
                      document.getElementById('post') || 
                      document.getElementById('article-container'));
    
    console.log("页面类型检测 - 是否为文章页:", isPostPage);
    
    // 只在非文章页面运行
    if (isPostPage) {
      console.log("检测到文章页面，跳过随机Banner设置");
      return;
    }
    
    console.log("检测到非文章页面，准备加载随机Banner");
    
    // 配置项
    const config = {
      // 图片尺寸
      width: 1920,
      height: 1080,
      
      // 图像来源配置
      imageSources: [
        {
          name: 'Picsum',
          weight: 20,  // 提高权重，确保优先选择
          // Picsum随机图片 - 确保每次请求都是唯一的
          getUrl: () => `https://picsum.photos/${config.width}/${config.height}?t=${Math.random()}`
        },
        {
          name: 'Unsplash',
          weight: 1,   // 降低权重，作为备用选项
          // Unsplash随机图片 - 确保每次请求都是唯一的
          getUrl: () => `https://source.unsplash.com/random/${config.width}x${config.height}?t=${Math.random()}`
        }
      ],
      
      // 默认图片（兜底方案）
      defaultImage: '/img/default_cover.jpg',
      
      // 降级超时时间（毫秒）
      timeout: 5000
    };
    
    /**
     * 找到页面头部元素
     */
    function findHeaderElement() {
      const headerElement = document.getElementById('page-header');
      
      if (headerElement) {
        console.log("找到Banner元素:", headerElement);
        return headerElement;
      }
      
      console.warn("未找到Banner元素");
      return null;
    }
    
    /**
     * 设置页面头部元素的背景图片
     */
    function setBackgroundImage(element, url) {
      if (!element) return;
      
      console.log(`正在设置Banner图片: ${url}`);
      element.style.backgroundImage = `url(${url})`;
      element.style.backgroundSize = 'cover';
      element.style.backgroundPosition = 'center';
      element.style.transition = 'background-image 0.5s ease-in-out';
      console.log(`Banner图片设置完成`);
    }
    
    /**
     * 使用指定图源加载图片
     */
    function loadImageFromSource(source) {
      return new Promise((resolve, reject) => {
        const url = source.getUrl();
        console.log(`尝试加载图片 (${source.name}): ${url}`);
        
        const img = new Image();
        
        // 设置超时
        const timeoutId = setTimeout(() => {
          reject(new Error(`从 ${source.name} 加载图片超时`));
        }, config.timeout);
        
        img.onload = function() {
          clearTimeout(timeoutId);
          console.log(`图片加载成功: ${url}`);
          resolve(url);
        };
        
        img.onerror = function() {
          clearTimeout(timeoutId);
          reject(new Error(`从 ${source.name} 加载图片失败`));
        };
        
        img.src = url;
      });
    }
    
    /**
     * 随机选择一个图像源（加权随机）
     */
    function getRandomImageSource() {
      // 计算权重总和
      const totalWeight = config.imageSources.reduce((sum, source) => sum + (source.weight || 1), 0);
      
      // 生成随机数
      let random = Math.floor(Math.random() * totalWeight);
      
      // 根据权重选择源
      for (const source of config.imageSources) {
        const weight = source.weight || 1;
        if (random < weight) {
          console.log(`选择图片源: ${source.name}`);
          return source;
        }
        random -= weight;
      }
      
      // 默认返回第一个源
      console.log(`默认选择图片源: ${config.imageSources[0].name}`);
      return config.imageSources[0];
    }
    
    /**
     * 尝试从随机源加载图片，失败时降级到其他源
     */
    function tryRandomImageSource(remainingSources) {
      // 如果没有剩余源，返回默认图片
      if (remainingSources.length === 0) {
        console.warn('所有图片源均失败，使用默认图片');
        return Promise.resolve(config.defaultImage);
      }
      
      // 随机选择一个索引
      const randomIndex = Math.floor(Math.random() * remainingSources.length);
      const source = remainingSources[randomIndex];
      
      // 从剩余源中移除这个源
      const newRemainingSources = [...remainingSources];
      newRemainingSources.splice(randomIndex, 1);
      
      // 尝试加载
      return loadImageFromSource(source)
        .catch(error => {
          console.warn(`${error.message}，尝试下一个图片源...`);
          // 当前源失败，尝试其他随机源
          return tryRandomImageSource(newRemainingSources);
        });
    }
    
    /**
     * 主函数：设置随机横幅图片
     */
    function setRandomBanner() {
      console.log('===== 开始设置随机Banner =====');
      
      // 获取页面头部元素
      const headerElement = findHeaderElement();
      if (!headerElement) {
        console.error('无法找到Banner元素');
        return;
      }
      
      // 始终先尝试使用Picsum
      const picsumSource = config.imageSources.find(source => source.name === 'Picsum');
      console.log('优先使用图片源: Picsum');
      
      // 先尝试加载Picsum
      loadImageFromSource(picsumSource)
        .then(url => {
          setBackgroundImage(headerElement, url);
        })
        .catch(error => {
          console.error('Picsum加载失败:', error);
          // Picsum失败后，尝试Unsplash
          const unsplashSource = config.imageSources.find(source => source.name === 'Unsplash');
          console.log('尝试备用图片源: Unsplash');
          
          loadImageFromSource(unsplashSource)
            .then(url => {
              setBackgroundImage(headerElement, url);
            })
            .catch(finalError => {
              console.error('所有图片源均失败:', finalError);
              setBackgroundImage(headerElement, config.defaultImage);
            });
        });
    }
    
    // 延迟一段时间再设置随机Banner，确保页面元素已加载
    setTimeout(setRandomBanner, 100);
  }
  
  // 确保在DOM加载完成后执行初始化函数
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM已经加载完成，可以直接执行
    init();
  }
  
  // 支持PJAX页面加载
  window.addEventListener('pjax:complete', init);
})(); 