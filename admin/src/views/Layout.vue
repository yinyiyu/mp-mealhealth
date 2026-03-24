<!-- views/Layout.vue - 主布局组件（含侧边栏、顶部导航） -->
<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarWidth" class="sidebar">
      <!-- Logo -->
      <div class="logo-area">
        <span class="logo-icon">🧠</span>
        <span v-show="!isCollapsed" class="logo-text">心理测评系统</span>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="$route.path"
        router
        :collapse="isCollapsed"
        background-color="#2C3E50"
        text-color="#BDC3C7"
        active-text-color="#FFFFFF"
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <i class="el-icon-odometer"></i>
          <span slot="title">数据看板</span>
        </el-menu-item>

        <el-menu-item
          v-if="isAdmin"
          index="/questionnaire"
        >
          <i class="el-icon-document"></i>
          <span slot="title">问卷管理</span>
        </el-menu-item>

        <el-menu-item
          v-if="isAdmin"
          index="/assessment"
        >
          <i class="el-icon-s-check"></i>
          <span slot="title">测评管理</span>
        </el-menu-item>

        <el-menu-item index="/statistics">
          <i class="el-icon-data-analysis"></i>
          <span slot="title">数据统计</span>
        </el-menu-item>

        <el-menu-item index="/student">
          <i class="el-icon-user"></i>
          <span slot="title">学生管理</span>
        </el-menu-item>

        <el-menu-item index="/followup">
          <i class="el-icon-bell"></i>
          <span slot="title">重点跟进</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主体区域 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <!-- 折叠侧边栏按钮 -->
        <i
          :class="isCollapsed ? 'el-icon-s-unfold' : 'el-icon-s-fold'"
          class="collapse-btn"
          @click="toggleSidebar"
        ></i>

        <!-- 面包屑 -->
        <el-breadcrumb separator="/" class="breadcrumb">
          <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>{{ $route.meta.title }}</el-breadcrumb-item>
        </el-breadcrumb>

        <!-- 右侧用户信息 -->
        <div class="header-right">
          <el-dropdown @command="onUserCommand">
            <div class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ userInfo ? userInfo.name[0] : '?' }}
              </el-avatar>
              <span class="user-name">{{ userInfo ? userInfo.name : '' }}</span>
              <i class="el-icon-arrow-down"></i>
            </div>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="profile">个人信息</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 页面内容 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'

export default {
  name: 'Layout',
  data() {
    return { isCollapsed: false }
  },
  computed: {
    ...mapState(['userInfo']),
    ...mapGetters(['isAdmin']),
    sidebarWidth() {
      return this.isCollapsed ? '64px' : '220px'
    }
  },
  methods: {
    ...mapActions(['logout']),
    toggleSidebar() {
      this.isCollapsed = !this.isCollapsed
    },
    onUserCommand(command) {
      if (command === 'logout') {
        this.$confirm('确认退出登录？', '提示', {
          confirmButtonText: '确认退出',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.logout()
          this.$router.push('/login')
          this.$message.success('已退出登录')
        }).catch(() => {})
      }
    }
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  background: #2C3E50;
  transition: width 0.3s;
  overflow: hidden;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  overflow: hidden;
  white-space: nowrap;
}

.logo-icon { font-size: 24px; margin-right: 10px; }
.logo-text { color: #FFFFFF; font-size: 16px; font-weight: 600; }

.sidebar-menu {
  border: none;
  height: calc(100vh - 60px);
}

/* 顶部导航 */
.header {
  background: #FFFFFF;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #EEEEEE;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #666666;
  margin-right: 16px;
}

.breadcrumb { flex: 1; }

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.user-avatar {
  background: #4A90D9;
  color: #FFFFFF;
  font-weight: 600;
}

.user-name { font-size: 14px; color: #333333; }

/* 主内容 */
.main-content {
  background: #F0F2F5;
  overflow-y: auto;
  padding: 20px;
}
</style>
