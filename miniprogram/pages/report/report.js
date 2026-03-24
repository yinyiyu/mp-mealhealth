// pages/report/report.js - 测评报告页面

const app = getApp()

Page({
  data: {
    // 页面模式：list（报告列表）或 detail（报告详情）
    mode: 'list',
    reports: [],       // 报告列表
    report: null,      // 当前查看的报告详情
    loading: false,
    page: 1,
    hasMore: true,
    // 风险等级中文映射
    riskLevelMap: {
      normal: { text: '心理状态正常', class: 'risk-normal', icon: '😊' },
      low_risk: { text: '低风险', class: 'risk-low', icon: '🟡' },
      medium_risk: { text: '中风险', class: 'risk-medium', icon: '🟠' },
      high_risk: { text: '高风险，需关注', class: 'risk-high', icon: '🔴' }
    }
  },

  onLoad(options) {
    if (!app.globalData.accessToken) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }

    if (options.report_id) {
      // 直接查看指定报告
      this.setData({ mode: 'detail' })
      this._loadReportDetail(options.report_id)
    } else if (options.assessment_id) {
      // 查看指定测评的我的报告
      this.setData({ mode: 'detail' })
      this._loadReportByAssessment(options.assessment_id)
    } else {
      // 查看历史报告列表
      this.setData({ mode: 'list' })
      this._loadReportList(true)
    }
  },

  onShow() {
    if (this.data.mode === 'list') {
      this._loadReportList(true)
    }
  },

  /**
   * 加载报告列表（历史记录）
   */
  _loadReportList(isRefresh = false) {
    if (this.data.loading) return
    const page = isRefresh ? 1 : this.data.page

    this.setData({ loading: true })
    app.request({
      url: `/report/my?page=${page}&per_page=10`,
      method: 'GET'
    }).then(res => {
      const newItems = res.data.items || []
      const reports = isRefresh ? newItems : [...this.data.reports, ...newItems]
      this.setData({
        reports,
        page: page + 1,
        hasMore: page < res.data.pages,
        loading: false
      })
    }).catch(() => this.setData({ loading: false }))
  },

  onReachBottom() {
    if (this.data.mode === 'list') this._loadReportList(false)
  },

  /**
   * 加载报告详情
   */
  _loadReportDetail(reportId) {
    this.setData({ loading: true })
    app.request({
      url: `/report/${reportId}`,
      method: 'GET'
    }).then(res => {
      this.setData({ report: res.data, loading: false })
      wx.setNavigationBarTitle({
        title: res.data.assessment_title || '测评报告'
      })
    }).catch(() => this.setData({ loading: false }))
  },

  _loadReportByAssessment(assessmentId) {
    // 先获取该测评的我的报告
    app.request({
      url: `/report/my?page=1&per_page=100`,
      method: 'GET'
    }).then(res => {
      const found = (res.data.items || []).find(
        r => r.assessment_id === parseInt(assessmentId)
      )
      if (found) {
        this._loadReportDetail(found.id)
      } else {
        this.setData({ loading: false })
        wx.showToast({ title: '未找到对应报告', icon: 'none' })
      }
    }).catch(() => this.setData({ loading: false }))
  },

  // 点击查看报告详情
  onReportTap(e) {
    const reportId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/report/report?report_id=${reportId}`
    })
  },

  // 返回列表
  onBackToList() {
    this.setData({ mode: 'list', report: null })
    this._loadReportList(true)
  },

  // 格式化日期
  formatDate(dateStr) {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
  },

  getRiskInfo(riskLevel) {
    return this.data.riskLevelMap[riskLevel] ||
      { text: '未知', class: '', icon: '❓' }
  }
})
