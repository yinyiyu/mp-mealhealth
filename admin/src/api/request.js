/**
 * api/request.js - Axios封装
 * 统一处理请求头、Token注入、错误处理、Token过期刷新
 */
import axios from 'axios'
import { Message } from 'element-ui'
import router from '../router'

// 创建Axios实例
const request = axios.create({
  baseURL: '/api',       // 开发环境通过vue.config.js代理到Flask
  timeout: 15000,        // 请求超时时间15秒
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器：自动注入JWT Token
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  response => {
    const { data } = response
    if (data.code === 200) {
      return data  // 成功返回数据
    }
    // 业务错误
    Message.error(data.message || '操作失败')
    return Promise.reject(new Error(data.message))
  },
  error => {
    if (error.response) {
      const { status } = error.response
      if (status === 401) {
        // Token无效或过期，清除登录状态跳转登录页
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_info')
        router.push('/login')
        Message.warning('登录已过期，请重新登录')
      } else if (status === 403) {
        Message.error('权限不足，无法执行此操作')
      } else if (status === 404) {
        Message.error('请求的资源不存在')
      } else {
        Message.error(`服务器错误：${status}`)
      }
    } else {
      Message.error('网络连接失败，请检查网络')
    }
    return Promise.reject(error)
  }
)

export default request
