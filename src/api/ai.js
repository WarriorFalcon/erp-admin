/**
 * AI 接口封装
 * 真实调用走 Django 后端（/api/ai/*），Django 后端转发至拓岳 New API
 * 拓岳 API 文档: https://docs.newapi.pro/zh/docs
 */

import axios from 'axios'

// ===================== 配置 =====================
const USE_MOCK = false  // 生产模式：关闭 mock，对接真实 API
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 90000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || error.message || 'AI 接口异常'
    console.error('[AI] 请求失败:', message)
    return Promise.reject(new Error(message))
  }
)

// ===================== Mock 数据（按商品名称动态返回） =====================
const MOCK_PRODUCT_DATA = {
  '女士连体泳装': {
    title: 'Women\'s One-Piece Swimsuit – Slim Fit Swimwear for Beach & Pool',
    description:
      '• High-quality polyester fabric, quick-dry & chlorine resistant\n' +
      '• Elegant one-piece design with slim-fit cut, flattering on all body types\n' +
      '• UPF 50+ sun protection, perfect for beach, pool, and waterpark\n' +
      '• Vintage-inspired vintage floral print, eye-catching and stylish\n' +
      '• Comfortable stretch material, no irritation on skin\n' +
      '• Available in multiple sizes: S–XL\n\n' +
      '【Product Details】\n' +
      'Material: 85% Polyester + 15% Spandex\n' +
      'Size: Refer to size chart (Asia sizing, runs small)\n' +
      'Color: Blue floral / Pink floral\n' +
      'Occasion: Beach, Pool, Waterpark, Vacation, Hot spring',
    description_cn:
      '【产品特点】\n' +
      '✨ 高品质涤纶面料，快干耐氯，适合多次使用\n' +
      '✨ 修身显瘦连体剪裁，修饰身材曲线\n' +
      '✨ UPF 50+ 防晒保护，海边/泳池必备\n' +
      '✨ 复古印花设计，时髦吸睛\n' +
      '✨ 弹力舒适面料，亲肤无刺激\n\n' +
      '【产品参数】\n' +
      '材质：85% 涤纶 + 15% 氨纶\n' +
      '尺码：S–XL（亚洲尺码偏小）\n' +
      '颜色：蓝花/粉花\n' +
      '适用场合：海边度假、游泳池、水上乐园、温泉',
  },
  '女士比基尼泳装': {
    title: 'Women\'s Bikini Set – Two-Piece Beach Swimwear for Summer Vacation',
    description:
      '• Soft and stretchy fabric, comfortable to wear all day\n' +
      '• V-neck top with adjustable straps, fits most body shapes\n' +
      '• Cheeky bottom coverage, trendy and flattering\n' +
      '• Fade-resistant colors, vibrant after multiple washes\n' +
      '• Perfect for beach, pool party, and tropical vacation\n' +
      '• Mix & match friendly, great as a gift\n\n' +
      '【Product Details】\n' +
      'Material: Nylon + Spandex blend\n' +
      'Size: S–XL\n' +
      'Style: Triangle bikini, adjustable\n' +
      'Occasion: Beach, Pool, Island vacation, Resort',
    description_cn:
      '【产品特点】\n' +
      '✨ 柔软弹力面料，全天舒适穿着\n' +
      '✨ V领可调节吊带，适配各种身材\n' +
      '✨ 经典比基尼版型，时髦显曲线\n' +
      '✨ 颜色持久鲜艳，多次洗涤不褪色\n' +
      '✨ 适合海滩、泳池派对、热带度假\n\n' +
      '【产品参数】\n' +
      '材质：锦纶+氨纶混纺\n' +
      '尺码：S–XL\n' +
      '款式：三角比基尼，可调节\n' +
      '适用场合：海滩度假、泳池派对、海岛游',
  },
  '儿童沙滩玩具套装': {
    title: 'Kids Beach Toys Set – Sand Mould & Water Play Set for Outdoor Fun',
    description:
      '• 10-piece sand toy set: bucket, shovel, rake, moulds, watering can & more\n' +
      '• Made of durable ABS plastic, non-toxic & safe for kids\n' +
      '• Bright vibrant colors, visually attractive to children\n' +
      '• Lightweight and portable, comes with a convenient carry bag\n' +
      '• Suitable for beach, sandbox, backyard, and water play\n' +
      '• Ideal gift for birthdays and summer holidays\n\n' +
      '【Product Details】\n' +
      'Material: ABS Plastic (BPA-free)\n' +
      'Pieces: 10 pieces per set\n' +
      'Age Range: 3–8 years old\n' +
      'Color: Multicolor\n' +
      'Occasion: Beach, Sandbox, Park, Backyard, Camping',
    description_cn:
      '【产品特点】\n' +
      '✨ 10件套沙滩玩具：水桶、铲子、耙子、模具、洒水壶等\n' +
      '✨ 优质 ABS 塑料，无毒安全，适合儿童\n' +
      '✨ 色彩鲜艳，吸引孩子注意力\n' +
      '✨ 轻便易携，附带收纳袋\n' +
      '✨ 沙滩、沙坑、后院、戏水通用\n\n' +
      '【产品参数】\n' +
      '材质：ABS 塑料（BPA-free）\n' +
      '件数：10件/套\n' +
      '适用年龄：3–8岁\n' +
      '颜色：多色混搭\n' +
      '适用场景：海边、沙滩、公园、露营',
  },
}

// ===================== Mock 卖点数据 =====================
const MOCK_FEATURES_DATA = {
  '女士连体泳装': [
    { icon: '🧵', title: '高品质面料', desc: '85%涤纶+15%氨纶，快干耐氯，弹力亲肤' },
    { icon: '✂️', title: '修身显瘦剪裁', desc: '高腰设计+侧面收紧，视觉显瘦10斤' },
    { icon: '☀️', title: 'UPF 50+防晒', desc: '有效阻挡98%紫外线，海边/泳池必备' },
    { icon: '🌸', title: '复古印花设计', desc: '时髦吸睛，出片率超高' },
    { icon: '📏', title: '多尺码可选', desc: 'S-XXL，亚洲女性专属尺码' },
  ],
  '女士比基尼泳装': [
    { icon: '👙', title: '可调节肩带', desc: '适应不同身材，稳稳托住不走光' },
    { icon: '💃', title: '显瘦V领设计', desc: '拉长脖颈线条，秒变天鹅颈' },
    { icon: '🌈', title: '色牢度高', desc: '多次洗涤依旧鲜艳如新' },
    { icon: '🎁', title: '送礼首选', desc: '精美礼盒包装，送闺蜜送女友超有面' },
    { icon: '🏖️', title: '多场景适用', desc: '海边/泳池/派对/温泉一衣多穿' },
  ],
  '儿童沙滩玩具套装': [
    { icon: '🧸', title: '10件套豪华配置', desc: '水桶+铲子+耙子+模具+洒水壶等' },
    { icon: '🔒', title: '安全无毒材质', desc: 'ABS食品级塑料，BPA-free认证' },
    { icon: '🎨', title: '色彩鲜艳', desc: '宝宝一眼爱上，主动丢掉手机平板' },
    { icon: '👶', title: '适用年龄广', desc: '3-8岁均适用，可玩到小学' },
    { icon: '🎒', title: '便携收纳袋', desc: '去海边/公园轻松收纳，走哪带哪' },
  ],
}

function getMockFeatures(name) {
  const n = name || ''
  for (const [key, features] of Object.entries(MOCK_FEATURES_DATA)) {
    if (n.includes(key) || key.includes(n)) return features
  }
  return MOCK_FEATURES_DATA['女士连体泳装']
}

// 根据商品名称关键字匹配 mock 数据
function getMockData(name) {
  const n = name || ''
  for (const [key, data] of Object.entries(MOCK_PRODUCT_DATA)) {
    if (n.includes(key) || key.includes(n)) return data
  }
  // 默认返回女士比基尼
  return MOCK_PRODUCT_DATA['女士比基尼泳装']
}

// ===================== Mock 图片库（按商品名称精确匹配） =====================
// 本地商品图片，按商品名称关键词精确匹配
const MOCK_IMAGE_LIB = {
  // 女士连体泳装
  lianti: [
    '/images/ladies/lianti/微信图片_20260412160439_925_65.jpg',
    '/images/ladies/lianti/微信图片_20260412160440_926_65.jpg',
    '/images/ladies/lianti/微信图片_20260412160441_927_65.jpg',
    '/images/ladies/lianti/微信图片_20260412160442_928_65.jpg',
  ],
  // 女士比基尼泳装
  bikini: [
    '/images/ladies/bikini/微信图片_20260412160430_922_65.jpg',
    '/images/ladies/bikini/微信图片_20260412160436_923_65.jpg',
    '/images/ladies/bikini/微信图片_20260412160437_924_65.jpg',
  ],
  // 儿童沙滩玩具套装
  toy: [
    '/images/toys/O1CN010FUwrw1e3m3lXVRZu_!!2201641843816-0-cib.jpg',
    '/images/toys/微信图片_20260412160425_919_65.jpg',
    '/images/toys/微信图片_20260412160426_920_65.jpg',
    '/images/toys/微信图片_20260412160427_921_65.jpg',
  ],
}

/**
 * 根据 prompt 关键词精确选择本地商品图片
 * @param {string} prompt - 用户输入的图片描述
 * @returns {string} 图片URL
 */
function getRelevantImage(prompt) {
  const p = (prompt || '').toLowerCase()

  // 女士连体泳装（优先匹配，因为关键词更具体）
  if (/连体泳装|one.*piece|one-piece/i.test(p)) {
    const lib = MOCK_IMAGE_LIB.lianti
    return lib[Math.floor(Math.random() * lib.length)]
  }
  // 女士比基尼泳装
  if (/比基尼|bikini|two.*piece/i.test(p)) {
    const lib = MOCK_IMAGE_LIB.bikini
    return lib[Math.floor(Math.random() * lib.length)]
  }
  // 儿童沙滩玩具套装
  if (/沙滩玩具|儿童沙滩|儿童玩具|玩具套装|sand.*toy|beach.*toy|toy.*set|kids.*toy/i.test(p)) {
    const lib = MOCK_IMAGE_LIB.toy
    return lib[Math.floor(Math.random() * lib.length)]
  }
  // 儿童/宝宝类 → 沙滩玩具
  if (/儿童|宝宝|小孩|kids|children|baby/i.test(p)) {
    const lib = MOCK_IMAGE_LIB.toy
    return lib[Math.floor(Math.random() * lib.length)]
  }
  // 女士泳装（兜底）
  if (/泳装|泳衣|swimsuit|swimwear|bathing suit|女士.*泳|woman.*swim/i.test(p)) {
    // 随机选连体或比基尼
    const all = [...MOCK_IMAGE_LIB.lianti, ...MOCK_IMAGE_LIB.bikini]
    return all[Math.floor(Math.random() * all.length)]
  }
  // 沙滩海边类 → 沙滩玩具
  if (/沙滩|海边|海滩|度假|beach|seaside|vacation|summer|outdoor/i.test(p)) {
    const lib = MOCK_IMAGE_LIB.toy
    return lib[Math.floor(Math.random() * lib.length)]
  }

  // 最兜底：返回随机泳装图片
  const all = [...MOCK_IMAGE_LIB.lianti, ...MOCK_IMAGE_LIB.bikini]
  return all[Math.floor(Math.random() * all.length)]
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// ===================== 核心接口 =====================

/**
 * 为商品生成标题（吸引点击）
 */
export async function generateTitle(goodsInfo) {
  if (USE_MOCK) {
    await delay(1000 + Math.random() * 1000)
    return getMockData(goodsInfo?.name)?.title || ''
  }

  const { name, category, material, style, features, targetMarket } = goodsInfo
  const res = await apiClient.post('/api/ai/generate-title/', {
    name,
    category,
    material: material || '',
    style: style || '',
    features: features || '',
    target_market: targetMarket || '跨境电商通用',
  })
  return res?.title || ''
}

/**
 * 为商品生成描述（促进转化）
 * @returns {{ description: string, description_cn: string }}
 */
export async function generateDescription(goodsInfo) {
  if (USE_MOCK) {
    await delay(1500 + Math.random() * 1000)
    const data = getMockData(goodsInfo?.name)
    return {
      description: data.description,
      description_cn: data.description_cn,
    }
  }

  const { name, category, material, style, features, specs, targetMarket } = goodsInfo
  const res = await apiClient.post('/api/ai/generate-description/', {
    name,
    category,
    material: material || '',
    style: style || '',
    features: features || '',
    specs: specs || '',
    target_market: targetMarket || '跨境电商通用',
  })
  return {
    description: res?.description || '',
    description_cn: res?.description_cn || ''
  }
}

/**
 * 改写/调整商品描述
 * @param {string} originalDesc - 原始英文描述
 * @param {string} adjustment - 调整方向（如"更短一些"、"更促销"、"突出材质"等中文描述）
 * @returns {{ description: string, description_cn: string }}
 */
export async function refineDescription(originalDesc, adjustment) {
  if (USE_MOCK) {
    await delay(1500 + Math.random() * 1000)
    // 模拟改写：在原描述基础上加个调整标记
    return {
      description: `[Adjusted per request "${adjustment}"]\n${originalDesc}`,
      description_cn: `已根据您的要求调整："${adjustment}"`,
    }
  }

  const res = await apiClient.post('/api/ai/refine-description/', {
    original_desc: originalDesc,
    adjustment: adjustment,
  })
  return {
    description: res?.description || '',
    description_cn: res?.description_cn || ''
  }
}

/**
 * 多语言翻译
 */
export async function translate(text, targetLang) {
  if (USE_MOCK) {
    await delay(600 + Math.random() * 400)
    return `[${targetLang.toUpperCase()}] ${text} (translated)`
  }

  const res = await apiClient.post('/api/ai/translate/', {
    text,
    target_lang: targetLang,
  })
  return res?.translation || ''
}

/**
 * AI 文生图（Nanobanana / Gemini）
 * @param {string} prompt - 图像描述
 * @returns {{ imageUrl: string, imageBase64: string }}
 */
export async function generateImage(prompt) {
  if (USE_MOCK) {
    await delay(3000 + Math.random() * 2000)
    // mock 文生图：根据 prompt 关键词智能返回对应商品图
    return {
      imageUrl: getRelevantImage(prompt),
      imageBase64: '',
    }
  }

  const res = await apiClient.post('/api/ai/image/generate/', { prompt })
  return {
    imageUrl: res?.image_url || '',
    imageBase64: res?.image_base64 || '',
  }
}

/**
 * AI 图生图（Nanobanana / Gemini）
 * @param {string} prompt - 图像修改指令
 * @param {string} imageBase64 - 原始图片 base64（data:image/xxx;base64,...）
 * @returns {{ imageUrl: string, imageBase64: string }}
 */
export async function editImage(prompt, imageBase64) {
  if (USE_MOCK) {
    await delay(4000 + Math.random() * 2000)
    // mock 图生图：根据修改指令关键词智能返回优化后的图片
    // 优化场景：白底、提亮、更清晰等 → 返回原商品图
    // 风格转换场景 → 返回对应的商品图
    return {
      imageUrl: getRelevantImage(prompt),
      imageBase64: '',
    }
  }

  const res = await apiClient.post('/api/ai/image/edit/', { prompt, image_base64: imageBase64 })
  return {
    imageUrl: res?.image_url || '',
    imageBase64: res?.image_base64 || '',
  }
}

/**
 * 为商品生成核心卖点（3-5条）
 * @param {object} goodsInfo - { name, category, ... }
 * @returns {Array<{icon, title, desc}>}
 */
export async function generateFeatures(goodsInfo) {
  if (USE_MOCK) {
    await delay(1200 + Math.random() * 800)
    return getMockFeatures(goodsInfo?.name)
  }

  const { name, category, material, style } = goodsInfo
  const res = await apiClient.post('/api/ai/generate-features/', {
    name,
    category: category || '',
    material: material || '',
    style: style || '',
  })
  return res?.features || []
}

// ===================== 拓岳AI对话（走后端代理，避免CORS）=====================
/**
 * 拓岳AI对话（通过Django后端代理）
 * @param {string[]} messages - 对话历史 [{role, content}, ...]
 * @param {string} systemPrompt - 系统提示词
 * @returns {Promise<string>} AI 回复文本
 */
export async function tuoyueChat(messages, systemPrompt = '') {
  console.log('[tuoyueChat] 调用 Django 后端代理...')

  try {
    const res = await apiClient.post('/api/ai/chat/', {
      messages,
      system_prompt: systemPrompt,
      temperature: 0.7,
      max_tokens: 800,
    })

    return res?.reply || ''
  } catch (err) {
    console.error('[tuoyueChat] 请求失败:', err.message)
    throw err
  }
}

export default {
  generateTitle,
  generateDescription,
  translate,
  generateImage,
  editImage,
  generateFeatures,
  tuoyueChat,
}
