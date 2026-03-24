/**
 * store/index.js - Vuex状态管理
 * 管理全局状态：用户信息、登录状态
 */
import Vue from 'vue'
import Vuex from 'vuex'
import { authApi } from '../api'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    // 当前登录用户信息
    userInfo: JSON.parse(localStorage.getItem('user_info') || 'null'),
    // JWT Token
    accessToken: localStorage.getItem('access_token') || null
  },

  getters: {
    // 是否已登录
    isLoggedIn: state => !!state.accessToken,
    // 当前用户角色
    userRole: state => state.userInfo?.role || '',
    // 是否为超级管理员
    isSuperAdmin: state => state.userInfo?.role === 'super_admin',
    // 是否为管理员（含超级管理员）
    isAdmin: state => ['admin', 'super_admin'].includes(state.userInfo?.role)
  },

  mutations: {
    // 设置登录信息
    SET_LOGIN(state, { accessToken, userInfo }) {
      state.accessToken = accessToken
      state.userInfo = userInfo
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('user_info', JSON.stringify(userInfo))
    },
    // 清除登录信息
    CLEAR_LOGIN(state) {
      state.accessToken = null
      state.userInfo = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
    }
  },

  actions: {
    /**
     * 登录操作
     * @param {Object} credentials - {username, password}
     */
    async login({ commit }, credentials) {
      const res = await authApi.login(credentials)
      commit('SET_LOGIN', {
        accessToken: res.data.access_token,
        userInfo: res.data.user
      })
      return res
    },

    /**
     * 退出登录
     */
    logout({ commit }) {
      commit('CLEAR_LOGIN')
    }
  }
})
