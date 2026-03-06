<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>产销平衡系统</h2>
        <p>Cement Production Balance System</p>
      </div>
      <a-form
        :model="formState"
        name="login"
        @finish="handleLogin"
        layout="vertical"
      >
        <a-form-item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input v-model:value="formState.username" placeholder="请输入用户名" size="large">
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password v-model:value="formState.password" placeholder="请输入密码" size="large">
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" block size="large" :loading="loading">
            登录
          </a-button>
        </a-form-item>
      </a-form>
      <div class="login-footer">
        <span class="text-muted">默认管理员: admin / admin-password</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { authApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const formState = reactive({
  username: '',
  password: '',
})

async function handleLogin() {
  loading.value = true
  try {
    const res = await authApi.login(formState.username, formState.password)
    userStore.setToken(res.access_token)
    
    // Get user info
    const user = await authApi.getMe()
    userStore.setUser(user)
    
    message.success('登录成功')
    router.push('/')
  } catch (error: any) {
    const msg = error.response?.data?.detail || '登录失败'
    message.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f0f2f5;
  background-image: url('https://gw.alipayobjects.com/zos/rmsportal/TVYTbAXWheQpRcWDaDMu.svg');
  background-repeat: no-repeat;
  background-position: center 110px;
  background-size: 100%;
}

.login-box {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 24px;
  color: #1f1f1f;
  margin-bottom: 8px;
  font-weight: 600;
}

.login-header p {
  color: #8c8c8c;
  font-size: 14px;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
  font-size: 12px;
  color: #8c8c8c;
}
</style>
