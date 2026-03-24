/**
 * api/index.js - 所有接口定义
 * 按模块分组：认证、问卷、测评、报告、学生、跟进、统计
 */
import request from './request'

// ============ 认证模块 ============
export const authApi = {
  // 账号密码登录
  login: (data) => request.post('/auth/login', data),
  // 获取当前用户信息
  getProfile: () => request.get('/auth/profile'),
  // 刷新Token
  refreshToken: () => request.post('/auth/refresh')
}

// ============ 问卷模板模块 ============
export const questionnaireApi = {
  // 获取问卷列表（支持分页和筛选）
  list: (params) => request.get('/questionnaire/', { params }),
  // 获取问卷详情（含题目）
  get: (id) => request.get(`/questionnaire/${id}`),
  // 创建问卷
  create: (data) => request.post('/questionnaire/', data),
  // 更新问卷
  update: (id, data) => request.put(`/questionnaire/${id}`, data),
  // 更新问卷状态（上架/下架）
  updateStatus: (id, status) => request.put(`/questionnaire/${id}/status`, { status }),
  // 删除问卷（仅草稿）
  delete: (id) => request.delete(`/questionnaire/${id}`),
  // 添加题目
  addQuestion: (templateId, data) => request.post(`/questionnaire/${templateId}/questions`, data),
  // 更新题目
  updateQuestion: (questionId, data) => request.put(`/questionnaire/questions/${questionId}`, data),
  // 删除题目
  deleteQuestion: (questionId) => request.delete(`/questionnaire/questions/${questionId}`)
}

// ============ 测评任务模块 ============
export const assessmentApi = {
  // 获取测评列表
  list: (params) => request.get('/assessment/', { params }),
  // 获取测评详情
  get: (id) => request.get(`/assessment/${id}`),
  // 创建测评
  create: (data) => request.post('/assessment/', data),
  // 更新测评状态（发布/结束）
  updateStatus: (id, status) => request.put(`/assessment/${id}/status`, { status })
}

// ============ 报告模块 ============
export const reportApi = {
  // 获取所有报告（管理员用）
  listAll: (params) => request.get('/report/list', { params }),
  // 获取报告详情
  get: (id) => request.get(`/report/${id}`),
  // 获取高风险学生列表
  getHighRisk: (params) => request.get('/report/high-risk', { params })
}

// ============ 学生管理模块 ============
export const studentApi = {
  // 获取学生列表
  list: (params) => request.get('/student/', { params }),
  // 获取学生详情
  get: (id) => request.get(`/student/${id}`),
  // 创建学生
  create: (data) => request.post('/student/', data),
  // 更新学生信息
  update: (id, data) => request.put(`/student/${id}`, data),
  // 删除学生
  delete: (id) => request.delete(`/student/${id}`),
  // 获取员工列表（老师/管理员）
  listStaff: () => request.get('/student/staff'),
  // 创建员工
  createStaff: (data) => request.post('/student/staff', data)
}

// ============ 跟进管理模块 ============
export const followupApi = {
  // 获取跟进记录列表
  list: (params) => request.get('/followup/', { params }),
  // 获取跟进记录详情
  get: (id) => request.get(`/followup/${id}`),
  // 创建跟进记录
  create: (data) => request.post('/followup/', data),
  // 更新跟进记录（状态、备注）
  update: (id, data) => request.put(`/followup/${id}`, data)
}

// ============ 统计模块 ============
export const statisticsApi = {
  // 系统概览数据
  overview: () => request.get('/statistics/overview'),
  // 指定测评统计
  assessment: (id) => request.get(`/statistics/assessment/${id}`),
  // 风险趋势
  riskTrend: (months = 6) => request.get('/statistics/risk-trend', { params: { months } }),
  // 跟进状态汇总
  followupSummary: () => request.get('/statistics/followup-summary')
}
