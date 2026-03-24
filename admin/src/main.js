/**
 * main.js - Vue应用入口文件
 * 初始化Vue、Element UI、路由、状态管理
 */
import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

// 注册Element UI（中文语言包）
import zhCN from 'element-ui/lib/locale/lang/zh-CN'
import locale from 'element-ui/lib/locale'
locale.use(zhCN)
Vue.use(ElementUI)

Vue.config.productionTip = false

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
