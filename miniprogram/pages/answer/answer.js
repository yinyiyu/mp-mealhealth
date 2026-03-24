// pages/answer/answer.js - 答题页面（核心功能页面）
// 负责展示题目、收集答案、计时、提交

const app = getApp()

Page({
  data: {
    // 测评信息
    assessmentId: null,
    assessmentTitle: '',
    submissionId: null,       // 答题记录ID
    questions: [],            // 所有题目
    totalQuestions: 0,

    // 答题进度
    currentIndex: 0,          // 当前题目索引（从0开始）
    answers: {},              // 已收集的答案 {question_id: answer}
    answeredCount: 0,         // 已答题目数

    // 计时器
    maxDurationMinutes: null, // 最大答题时长
    elapsedSeconds: 0,        // 已用秒数
    timerText: '00:00',       // 显示的计时文字
    isOvertime: false,        // 是否超时

    // UI状态
    loading: true,
    submitting: false,
    showProgress: false       // 是否显示进度条（侧边栏）
  },

  _timer: null,   // 计时器句柄（不放在data中，避免不必要的更新）

  onLoad(options) {
    const { assessment_id, title } = options
    this.setData({
      assessmentId: parseInt(assessment_id),
      assessmentTitle: decodeURIComponent(title || '心理测评')
    })
    wx.setNavigationBarTitle({ title: decodeURIComponent(title || '心理测评') })

    this._startAssessment()
  },

  onUnload() {
    // 页面卸载时清除计时器，防止内存泄漏
    if (this._timer) {
      clearInterval(this._timer)
    }
  },

  /**
   * 开始答题：调用接口创建答题记录，加载题目
   */
  _startAssessment() {
    app.request({
      url: `/assessment/${this.data.assessmentId}/start`,
      method: 'POST'
    }).then(res => {
      const { submission_id, answers_data, max_duration_minutes } = res.data
      this.setData({ submissionId: submission_id })

      // 加载测评详情（包含题目列表）
      return app.request({
        url: `/assessment/${this.data.assessmentId}`,
        method: 'GET'
      }).then(detailRes => {
        const questions = detailRes.data.template?.questions || []

        // 恢复已保存的答题进度
        const savedAnswers = answers_data || {}
        const answeredCount = Object.keys(savedAnswers).length

        this.setData({
          questions,
          totalQuestions: questions.length,
          answers: savedAnswers,
          answeredCount,
          maxDurationMinutes: max_duration_minutes,
          loading: false
        })

        // 启动计时器
        if (max_duration_minutes) {
          this._startTimer(max_duration_minutes * 60)
        }
      })
    }).catch(() => {
      this.setData({ loading: false })
      wx.navigateBack()
    })
  },

  /**
   * 启动倒计时器
   * @param {number} totalSeconds - 总答题秒数
   */
  _startTimer(totalSeconds) {
    this._timer = setInterval(() => {
      const elapsed = this.data.elapsedSeconds + 1
      const remaining = totalSeconds - elapsed

      if (remaining <= 0) {
        // 超时，自动提交
        clearInterval(this._timer)
        this.setData({ elapsedSeconds: elapsed, isOvertime: true })
        wx.showToast({ title: '答题超时，即将自动提交', icon: 'none', duration: 2000 })
        setTimeout(() => this._doSubmit(), 2000)
        return
      }

      // 格式化剩余时间显示
      const mins = Math.floor(remaining / 60)
      const secs = remaining % 60
      const timerText = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`

      this.setData({ elapsedSeconds: elapsed, timerText })

      // 剩余5分钟时提醒
      if (remaining === 300) {
        wx.showToast({ title: '还剩5分钟，请加快作答', icon: 'none' })
      }
    }, 1000)
  },

  /**
   * 学生选择答案
   * @param {Event} e - 点击事件，携带 question_id 和 option_label
   */
  onSelectOption(e) {
    const { questionId, optionLabel, questionType } = e.currentTarget.dataset
    const questionIdStr = String(questionId)
    const currentAnswers = { ...this.data.answers }

    if (questionType === 'single_choice') {
      // 单选：直接设置选项
      currentAnswers[questionIdStr] = optionLabel
    } else if (questionType === 'multiple_choice') {
      // 多选：切换选中状态
      const current = currentAnswers[questionIdStr] || []
      const index = current.indexOf(optionLabel)
      if (index >= 0) {
        current.splice(index, 1)  // 取消选中
      } else {
        current.push(optionLabel)  // 选中
      }
      currentAnswers[questionIdStr] = [...current]
    }

    const answeredCount = Object.keys(currentAnswers).filter(
      k => currentAnswers[k] !== null &&
           currentAnswers[k] !== undefined &&
           (Array.isArray(currentAnswers[k]) ? currentAnswers[k].length > 0 : true)
    ).length

    this.setData({ answers: currentAnswers, answeredCount })

    // 单选自动跳到下一题
    if (questionType === 'single_choice') {
      setTimeout(() => this._goToNext(), 300)
    }
  },

  // 上一题
  onPrev() {
    if (this.data.currentIndex > 0) {
      this.setData({ currentIndex: this.data.currentIndex - 1 })
    }
  },

  // 下一题（或提交）
  onNext() {
    const { currentIndex, totalQuestions } = this.data
    if (currentIndex < totalQuestions - 1) {
      this._goToNext()
    } else {
      this._confirmSubmit()
    }
  },

  _goToNext() {
    const { currentIndex, totalQuestions } = this.data
    if (currentIndex < totalQuestions - 1) {
      this.setData({ currentIndex: currentIndex + 1 })
      // 自动暂存进度（每答5题保存一次）
      if (currentIndex % 5 === 4) {
        this._saveProgress()
      }
    }
  },

  // 跳转到指定题目（点击进度栏）
  onJumpToQuestion(e) {
    this.setData({
      currentIndex: e.currentTarget.dataset.index,
      showProgress: false
    })
  },

  // 切换进度面板
  toggleProgress() {
    this.setData({ showProgress: !this.data.showProgress })
  },

  /**
   * 暂存答题进度（网络请求，非关键路径，失败不影响答题）
   */
  _saveProgress() {
    if (!this.data.submissionId) return
    app.request({
      url: `/assessment/submissions/${this.data.submissionId}/save`,
      method: 'PUT',
      data: { answers: this.data.answers }
    }).catch(() => {})  // 暂存失败不提示用户
  },

  /**
   * 提交前确认
   */
  _confirmSubmit() {
    const { totalQuestions, answeredCount } = this.data
    const unanswered = totalQuestions - answeredCount

    if (unanswered > 0) {
      wx.showModal({
        title: '还有题目未作答',
        content: `您还有 ${unanswered} 道题目未回答，是否确认提交？`,
        confirmText: '确认提交',
        cancelText: '继续作答',
        success: (res) => {
          if (res.confirm) this._doSubmit()
        }
      })
    } else {
      wx.showModal({
        title: '确认提交',
        content: '所有题目已完成，确认提交测评？',
        confirmText: '立即提交',
        cancelText: '再检查一下',
        success: (res) => {
          if (res.confirm) this._doSubmit()
        }
      })
    }
  },

  /**
   * 执行提交答题
   */
  _doSubmit() {
    if (this.data.submitting) return
    if (this._timer) clearInterval(this._timer)

    this.setData({ submitting: true })

    app.request({
      url: `/assessment/submissions/${this.data.submissionId}/submit`,
      method: 'POST',
      data: { answers: this.data.answers }
    }).then(res => {
      const { report_id, total_score, risk_level_text } = res.data
      wx.showModal({
        title: '测评完成 🎉',
        content: `您的测评已提交成功！\n得分：${total_score}分\n风险等级：${risk_level_text}`,
        showCancel: false,
        confirmText: '查看详细报告',
        success: () => {
          wx.redirectTo({
            url: `/pages/report/report?report_id=${report_id}`
          })
        }
      })
    }).catch(() => {
      this.setData({ submitting: false })
      if (this.data.maxDurationMinutes) {
        this._startTimer((this.data.maxDurationMinutes * 60) - this.data.elapsedSeconds)
      }
    })
  },

  // 检查指定题目是否已回答
  isAnswered(questionId) {
    const ans = this.data.answers[String(questionId)]
    if (Array.isArray(ans)) return ans.length > 0
    return ans !== undefined && ans !== null
  },

  // 检查选项是否被选中
  isOptionSelected(questionId, optionLabel) {
    const ans = this.data.answers[String(questionId)]
    if (Array.isArray(ans)) return ans.includes(optionLabel)
    return ans === optionLabel
  }
})
