// pages/profile/profile.js - 个人信息页面

const app = getApp()

Page({
  data: {
    userInfo: null,
    editing: false,
    form: {},
    loading: false,
    mode: ''  // 'complete' = 新用户完善信息
  },

  onLoad(options) {
    if (!app.globalData.accessToken) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    const userInfo = app.globalData.userInfo
    this.setData({
      userInfo,
      form: { ...userInfo },
      mode: options.mode || ''
    })

    if (options.mode === 'complete') {
      this.setData({ editing: true })
      wx.setNavigationBarTitle({ title: '完善个人信息' })
    }
  },

  onEditToggle() {
    this.setData({
      editing: !this.data.editing,
      form: { ...this.data.userInfo }
    })
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    const form = { ...this.data.form }
    form[field] = e.detail.value
    this.setData({ form })
  },

  onSave() {
    const { form } = this.data
    if (!form.name?.trim()) {
      wx.showToast({ title: '姓名不能为空', icon: 'none' })
      return
    }

    this.setData({ loading: true })
    app.request({
      url: '/auth/profile',
      method: 'PUT',
      data: {
        name: form.name,
        student_id: form.student_id,
        department: form.department,
        grade: form.grade,
        phone: form.phone,
        email: form.email
      }
    }).then(res => {
      // 更新全局用户信息
      app.globalData.userInfo = res.data
      wx.setStorageSync('user_info', res.data)
      this.setData({
        userInfo: res.data,
        editing: false,
        loading: false
      })
      wx.showToast({ title: '保存成功', icon: 'success' })

      // 新用户完善信息后跳到首页
      if (this.data.mode === 'complete') {
        wx.switchTab({ url: '/pages/assessment/assessment' })
      }
    }).catch(() => this.setData({ loading: false }))
  },

  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确认退出当前账号？',
      success: (res) => {
        if (res.confirm) {
          app.logout()
        }
      }
    })
  }
})
