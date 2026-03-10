<template>
  <div id="app">
    <el-container>
      <!-- 左侧菜单 -->
      <el-aside width="200px">
        <div class="logo">
          <h2>🏛️ 朝廷政务</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#F5F7FA"
          text-color="#303133"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <el-icon><DataAnalysis /></el-icon>
            <span>📊 总览</span>
          </el-menu-item>
          <el-menu-item index="/ministers">
            <el-icon><User /></el-icon>
            <span>👥 大臣</span>
          </el-menu-item>
          <el-menu-item index="/tasks">
            <el-icon><Document /></el-icon>
            <span>📋 任务</span>
          </el-menu-item>
          <el-menu-item index="/flows">
            <el-icon><Connection /></el-icon>
            <span>🔗 流转</span>
          </el-menu-item>
          <el-menu-item index="/stats">
            <el-icon><TrendCharts /></el-icon>
            <span>📈 报表</span>
          </el-menu-item>
          <el-menu-item index="/config">
            <el-icon><Setting /></el-icon>
            <span>⚙️ 配置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 右侧内容 -->
      <el-container>
        <!-- 顶部栏 -->
        <el-header>
          <div class="header-content">
            <h3>朝廷政务管理系统</h3>
            <div class="user-info">
              <el-avatar :size="32" icon="User" />
              <span>皇上</span>
              <el-button type="danger" size="small" @click="logout">退出</el-button>
            </div>
          </div>
        </el-header>

        <!-- 主内容区 -->
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => route.path)

const logout = () => {
  // TODO: 实现退出登录
  console.log('退出登录')
}
</script>

<style scoped>
#app {
  height: 100vh;
}

.el-container {
  height: 100%;
}

.el-aside {
  background-color: #F5F7FA;
  border-right: 1px solid #E4E7ED;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #E4E7ED;
}

.logo h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.el-header {
  background-color: #FFFFFF;
  border-bottom: 1px solid #E4E7ED;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.el-main {
  background-color: #F5F7FA;
  padding: 20px;
}
</style>
