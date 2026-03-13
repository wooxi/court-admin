import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import {
  ArrowRight,
  Bottom,
  CircleCheck,
  Clock,
  Connection,
  Cpu,
  DataAnalysis,
  Document,
  Download,
  Expand,
  Fold,
  Plus,
  Refresh,
  Right,
  Setting,
  Timer,
  Top,
  TrendCharts,
  User,
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

const iconMap = {
  ArrowRight,
  Bottom,
  CircleCheck,
  Clock,
  Connection,
  Cpu,
  DataAnalysis,
  Document,
  Download,
  Expand,
  Fold,
  Plus,
  Refresh,
  Right,
  Setting,
  Timer,
  Top,
  TrendCharts,
  User,
}

Object.entries(iconMap).forEach(([name, component]) => {
  app.component(name, component)
})

app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

app.mount('#app')
