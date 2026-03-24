// app.js - 小程序全局入口文件
// 负责初始化应用、管理全局状态（登录信息、请求拦截等）

App({
  // 全局数据（整个小程序共享）
  globalData: {
    userInfo: null,          // 当前登录用户信息
    accessToken: null,       // JWT访问Token
    refreshToken: null,      // JWT刷新Token
    // 后端API基础地址，开发环境指向本地，生产环境改为服务器地址
    baseUrl: 'http://localhost:5000/api'
  },

  /**
   * 小程序启动时执行
   */
  onLaunch() {
    // 从本地缓存恢复登录状态（用户上次登录的Token）
    const token = wx.getStorageSync('access_token')
    const userInfo = wx.getStorageSync('user_info')
    if (token) {
      this.globalData.accessToken = token
      this.globalData.userInfo = userInfo
    }
  },

  /**
   * 封装HTTP请求方法（统一处理Token、错误等）
   * 使用方法：
   *   const app = getApp()
   *   app.request({ url: '/questionnaire/', method: 'GET' }).then(res => {...})
   *
   * @param {Object} options - 请求参数
   * @param {string} options.url - 接口路径（相对于baseUrl）
   * @param {string} options.method - 请求方法（GET/POST/PUT/DELETE）
   * @param {Object} options.data - 请求参数
   * @param {boolean} options.noAuth - 是否不需要Token（如登录接口）
   */
  request(options) {
    const { url, method = 'GET', data = {}, noAuth = false } = options
    const fullUrl = this.globalData.baseUrl + url

    // 构建请求头
    const header = { 'Content-Type': 'application/json' }
    if (!noAuth && this.globalData.accessToken) {
      header['Authorization'] = `Bearer ${this.globalData.accessToken}`
    }

    return new Promise((resolve, reject) => {
      wx.request({
        url: fullUrl,
        method,
        data,
        header,
        success: (res) => {
          if (res.statusCode === 401) {
            // Token过期，跳转登录页
            wx.removeStorageSync('access_token')
            wx.removeStorageSync('user_info')
            this.globalData.accessToken = null
            this.globalData.userInfo = null
            wx.redirectTo({ url: '/pages/login/login' })
            reject(new Error('请重新登录'))
            return
          }
          if (res.data.code === 200) {
            resolve(res.data)
          } else {
            // 业务错误（接口返回非200 code）
            wx.showToast({
              title: res.data.message || '请求失败',
              icon: 'none',
              duration: 2000
            })
            reject(new Error(res.data.message))
          }
        },
        fail: (err) => {
          wx.showToast({ title: '网络请求失败，请检查网络', icon: 'none' })
          reject(err)
        }
      })
    })
  },

  /**
   * 保存登录信息到本地缓存
   */
  saveLoginInfo(accessToken, refreshToken, userInfo) {
    this.globalData.accessToken = accessToken
    this.globalData.refreshToken = refreshToken
    this.globalData.userInfo = userInfo
    wx.setStorageSync('access_token', accessToken)
    wx.setStorageSync('refresh_token', refreshToken)
    wx.setStorageSync('user_info', userInfo)
  },

  /**
   * 退出登录
   */
  logout() {
    this.globalData.accessToken = null
    this.globalData.refreshToken = null
    this.globalData.userInfo = null
    wx.removeStorageSync('access_token')
    wx.removeStorageSync('refresh_token')
    wx.removeStorageSync('user_info')
    wx.redirectTo({ url: '/pages/login/login' })
  }
})
