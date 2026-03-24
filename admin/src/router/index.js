/**
 * router/index.js - Vue Router路由配置
 * 配置各页面的路由和导航守卫（权限控制）
 */
import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const routes = [
  // 登录页（无需认证）
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', noAuth: true }
  },
  // 主布局（含侧边栏、顶部导航）
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      // 首页（数据看板）
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '数据看板', icon: 'el-icon-odometer' }
      },
      // 问卷管理
      {
        path: '/questionnaire',
        name: 'Questionnaire',
        component: () => import('../views/questionnaire/QuestionnaireList.vue'),
        meta: { title: '问卷管理', icon: 'el-icon-document', roles: ['admin', 'super_admin'] }
      },
      {
        path: '/questionnaire/create',
        name: 'QuestionnaireCreate',
        component: () => import('../views/questionnaire/QuestionnaireEdit.vue'),
        meta: { title: '创建问卷', roles: ['admin', 'super_admin'] }
      },
      {
        path: '/questionnaire/edit/:id',
        name: 'QuestionnaireEdit',
        component: () => import('../views/questionnaire/QuestionnaireEdit.vue'),
        meta: { title: '编辑问卷', roles: ['admin', 'super_admin'] }
      },
      // 测评管理
      {
        path: '/assessment',
        name: 'Assessment',
        component: () => import('../views/assessment/AssessmentList.vue'),
        meta: { title: '测评管理', icon: 'el-icon-s-check', roles: ['admin', 'super_admin'] }
      },
      {
        path: '/assessment/create',
        name: 'AssessmentCreate',
        component: () => import('../views/assessment/AssessmentEdit.vue'),
        meta: { title: '发布测评', roles: ['admin', 'super_admin'] }
      },
      {
        path: '/assessment/:id/statistics',
        name: 'AssessmentStatistics',
        component: () => import('../views/statistics/AssessmentStats.vue'),
        meta: { title: '测评统计', roles: ['admin', 'super_admin', 'teacher'] }
      },
      // 数据统计
      {
        path: '/statistics',
        name: 'Statistics',
        component: () => import('../views/statistics/Overview.vue'),
        meta: { title: '数据统计', icon: 'el-icon-data-analysis' }
      },
      // 学生管理
      {
        path: '/student',
        name: 'Student',
        component: () => import('../views/student/StudentList.vue'),
        meta: { title: '学生管理', icon: 'el-icon-user' }
      },
      // 重点跟进
      {
        path: '/followup',
        name: 'FollowUp',
        component: () => import('../views/followup/FollowUpList.vue'),
        meta: { title: '重点跟进', icon: 'el-icon-bell' }
      }
    ]
  },
  // 404页面
  { path: '*', redirect: '/dashboard' }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

/**
 * 全局路由守卫：检查登录状态和角色权限
 */
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || '管理后台'} - 心理健康测评系统`

  // 无需认证的页面直接放行
  if (to.meta.noAuth) {
    next()
    return
  }

  // 检查是否已登录
  const token = localStorage.getItem('access_token')
  if (!token) {
    next('/login')
    return
  }

  // 检查角色权限
  const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}')
  const requiredRoles = to.meta.roles
  if (requiredRoles && !requiredRoles.includes(userInfo.role)) {
    next('/dashboard')  // 无权限跳转首页
    return
  }

  next()
})

export default router
