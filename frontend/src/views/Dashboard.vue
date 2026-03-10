<template>
  <div class="dashboard">
    <h1>📊 总览</h1>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #409EFF;">
              <el-icon :size="30"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.ministers }}</div>
              <div class="stat-label">大臣数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #67C23A;">
              <el-icon :size="30"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.tasks }}</div>
              <div class="stat-label">任务总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #E6A23C;">
              <el-icon :size="30"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.tokens }}</div>
              <div class="stat-label">Token 用量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card>
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #F56C6C;">
              <el-icon :size="30"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completionRate }}%</div>
              <div class="stat-label">完成率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>⚡ 快捷操作</span>
        </div>
      </template>
      <el-button type="primary" @click="$router.push('/tasks')">创建任务</el-button>
      <el-button type="success" @click="$router.push('/ministers')">大臣配置</el-button>
      <el-button type="warning" @click="$router.push('/stats')">查看报表</el-button>
      <el-button type="info" @click="$router.push('/config')">系统配置</el-button>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stats = ref({
  ministers: 7,
  tasks: 0,
  tokens: 0,
  completionRate: 0
})

onMounted(async () => {
  // TODO: 从 API 加载真实数据
  stats.value = {
    ministers: 7,
    tasks: 238,
    tokens: '446k',
    completionRate: 86.1
  }
})
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 20px;
  color: #303133;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
