// pages/login/login.js - 登录页面逻辑

const app = getApp()

Page({
  data: {
    // 表单数据
    username: '',
    password: '',
    // UI状态
    loading: false,
    loginMode: 'wechat',   // 登录方式：wechat（微信一键登录）或 account（账号密码）
  },

  onLoad() {
    // 如果已经登录，直接跳转首页
    if (app.globalData.accessToken && app.globalData.userInfo) {
      wx.switchTab({ url: '/pages/assessment/assessment' })
    }
  },

  /**
   * 微信一键登录
   * 调用wx.login()获取临时code，发给后端换取Token
   */
  onWechatLogin() {
    if (this.data.loading) return
    this.setData({ loading: true })

    wx.login({
      success: (loginRes) => {
        if (!loginRes.code) {
          wx.showToast({ title: '微信登录失败，请重试', icon: 'none' })
          this.setData({ loading: false })
          return
        }

        // 获取用户信息（微信新版本已不允许直接获取用户信息，这里使用基础登录）
        app.request({
          url: '/auth/wechat-login',
          method: 'POST',
          noAuth: true,
          data: { code: loginRes.code }
        }).then(res => {
          // 保存登录信息
          app.saveLoginInfo(
            res.data.access_token,
            res.data.refresh_token,
            res.data.user
          )

          // 新用户需要完善信息
          if (res.data.is_new_user) {
            wx.navigateTo({ url: '/pages/profile/profile?mode=complete' })
          } else {
            wx.switchTab({ url: '/pages/assessment/assessment' })
          }
        }).catch(() => {
          this.setData({ loading: false })
        }).finally(() => {
          this.setData({ loading: false })
        })
      },
      fail: () => {
        wx.showToast({ title: '微信授权失败', icon: 'none' })
        this.setData({ loading: false })
      }
    })
  },

  /**
   * 账号密码登录（老师/管理员也可以通过此方式登录）
   */
  onAccountLogin() {
    const { username, password } = this.data

    if (!username.trim()) {
      wx.showToast({ title: '请输入用户名', icon: 'none' })
      return
    }
    if (!password) {
      wx.showToast({ title: '请输入密码', icon: 'none' })
      return
    }

    this.setData({ loading: true })

    app.request({
      url: '/auth/login',
      method: 'POST',
      noAuth: true,
      data: { username: username.trim(), password }
    }).then(res => {
      app.saveLoginInfo(
        res.data.access_token,
        res.data.refresh_token,
        res.data.user
      )
      wx.switchTab({ url: '/pages/assessment/assessment' })
    }).catch(() => {
      this.setData({ loading: false })
    })
  },

  // 切换登录方式
  switchLoginMode(e) {
    this.setData({ loginMode: e.currentTarget.dataset.mode })
  },

  // 输入框事件
  onUsernameInput(e) { this.setData({ username: e.detail.value }) },
  onPasswordInput(e) { this.setData({ password: e.detail.value }) }
})
