// pages/assessment/assessment.js - 测评列表页面

const app = getApp()

Page({
  data: {
    assessments: [],       // 测评列表数据
    completedIds: [],      // 已完成的测评ID列表
    loading: false,
    refreshing: false,     // 下拉刷新状态
    page: 1,
    hasMore: true,         // 是否还有更多数据
    userInfo: null         // 当前用户信息
  },

  onLoad() {
    // 检查是否已登录
    if (!app.globalData.accessToken) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    this.setData({ userInfo: app.globalData.userInfo })
    this.loadAssessments(true)
  },

  onShow() {
    // 每次显示页面时刷新列表（处理完成答题后回到列表的情况）
    this.loadAssessments(true)
  },

  /**
   * 加载测评列表
   * @param {boolean} isRefresh - 是否刷新（重置到第一页）
   */
  loadAssessments(isRefresh = false) {
    if (this.data.loading) return

    if (isRefresh) {
      this.setData({ page: 1, hasMore: true })
    }

    if (!this.data.hasMore && !isRefresh) return

    this.setData({ loading: true })

    const page = isRefresh ? 1 : this.data.page

    app.request({
      url: `/assessment/?page=${page}&per_page=10`,
      method: 'GET'
    }).then(res => {
      const newItems = res.data.items || []
      const assessments = isRefresh ? newItems : [...this.data.assessments, ...newItems]

      this.setData({
        assessments,
        completedIds: res.data.completed_ids || [],
        page: page + 1,
        hasMore: page < res.data.pages,
        loading: false,
        refreshing: false
      })
    }).catch(() => {
      this.setData({ loading: false, refreshing: false })
    })
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.setData({ refreshing: true })
    this.loadAssessments(true)
    wx.stopPullDownRefresh()
  },

  // 上拉加载更多
  onReachBottom() {
    this.loadAssessments(false)
  },

  /**
   * 点击测评卡片
   * - 已完成：查看报告
   * - 未完成：进入答题
   */
  onAssessmentTap(e) {
    const assessment = e.currentTarget.dataset.item
    const isCompleted = this.data.completedIds.includes(assessment.id)

    if (isCompleted) {
      // 已完成，跳转到报告页
      wx.navigateTo({
        url: `/pages/report/report?assessment_id=${assessment.id}`
      })
    } else {
      // 未完成，跳转答题页
      wx.navigateTo({
        url: `/pages/answer/answer?assessment_id=${assessment.id}&title=${encodeURIComponent(assessment.title)}`
      })
    }
  },

  /**
   * 格式化时间显示
   */
  formatTime(time) {
    if (!time) return '不限'
    const date = new Date(time)
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  }
})
