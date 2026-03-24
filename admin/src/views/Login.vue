<!-- views/Login.vue - 管理后台登录页面 -->
<template>
  <div class="login-page">
    <div class="login-box">
      <!-- 标题 -->
      <div class="login-header">
        <h1 class="title">心理健康测评系统</h1>
        <p class="subtitle">管理后台</p>
      </div>

      <!-- 登录表单 -->
      <el-form
        ref="loginForm"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.native.prevent="onSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="el-icon-user"
            size="medium"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="el-icon-lock"
            size="medium"
            show-password
            @keyup.enter.native="onSubmit"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="medium"
          :loading="loading"
          style="width: 100%; margin-top: 8px;"
          @click="onSubmit"
        >
          {{ loading ? '登录中...' : '登录' }}
        </el-button>
      </el-form>

      <!-- 提示 -->
      <p class="hint">默认账号：admin / Admin@123</p>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'Login',
  data() {
    return {
      form: { username: '', password: '' },
      loading: false,
      rules: {
        username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
        password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
      }
    }
  },
  created() {
    // 已登录则直接跳转
    if (localStorage.getItem('access_token')) {
      this.$router.push('/')
    }
  },
  methods: {
    ...mapActions(['login']),
    onSubmit() {
      this.$refs.loginForm.validate(async (valid) => {
        if (!valid) return
        this.loading = true
        try {
          await this.login(this.form)
          this.$message.success('登录成功')
          this.$router.push('/dashboard')
        } finally {
          this.loading = false
        }
      })
    }
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #4A90D9 0%, #2C3E50 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-box {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 48px 40px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: #1A1A1A;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  color: #888888;
}

.hint {
  text-align: center;
  font-size: 12px;
  color: #BBBBBB;
  margin-top: 16px;
}
</style>
