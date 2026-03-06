import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App.vue'
import router from './router'
import './styles/global.css'
import { useAppStore } from './stores/app'

const app = createApp(App)
const pinia = createPinia()
dayjs.locale('zh-cn')
app.use(pinia)
app.use(router)
app.use(Antd)
useAppStore(pinia).initTheme()
app.mount('#app')
