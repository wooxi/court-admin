<template>
  <div class="ministers">
    <div class="page-header">
      <h1>👥 大臣配置</h1>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        添加大臣
      </el-button>
    </div>

    <!-- 大臣列表 -->
    <el-card v-for="minister in ministers" :key="minister.id" style="margin-bottom: 20px;">
      <div class="minister-card">
        <div class="minister-header">
          <div class="minister-info">
            <h3>{{ minister.name }}</h3>
            <el-tag :type="minister.enabled ? 'success' : 'info'">
              {{ minister.enabled ? '✅ 已启用' : '❌ 已禁用' }}
            </el-tag>
          </div>
          <div class="minister-actions">
            <el-button size="small" @click="editMinister(minister)">编辑</el-button>
            <el-button size="small" :type="minister.enabled ? 'warning' : 'success'" @click="toggleMinister(minister)">
              {{ minister.enabled ? '禁用' : '启用' }}
            </el-button>
          </div>
        </div>
        
        <el-descriptions :column="3" border>
          <el-descriptions-item label="部门">{{ minister.department }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ minister.model_id }}</el-descriptions-item>
          <el-descriptions-item label="工作区">{{ minister.workspace }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showAddDialog" title="编辑大臣配置" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="大臣名称">
          <el-select v-model="form.name" placeholder="选择大臣">
            <el-option label="司礼监" value="司礼监" />
            <el-option label="兵部" value="兵部" />
            <el-option label="户部" value="户部" />
            <el-option label="礼部" value="礼部" />
            <el-option label="工部" value="工部" />
            <el-option label="吏部" value="吏部" />
            <el-option label="刑部" value="刑部" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="部门">
          <el-input v-model="form.department" placeholder="所属部门" />
        </el-form-item>
        
        <el-form-item label="模型">
          <el-select v-model="form.model_id" placeholder="选择模型" loading={loadingModels}>
            <el-option
              v-for="model in availableModels"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            >
              {{ model.name }} (上下文：{{ model.contextWindow }})
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="工作区">
          <el-input v-model="form.workspace" placeholder="/root/clawd" />
        </el-form-item>
        
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMinister">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const ministers = ref([])
const availableModels = ref([])
const loadingModels = ref(false)
const showAddDialog = ref(false)
const form = ref({
  name: '',
  department: '',
  model_id: '',
  workspace: '',
  enabled: true
})

// 加载大臣列表
const loadMinisters = async () => {
  try {
    const data = await api.get('/ministers/')
    ministers.value = data
  } catch (error) {
    console.error('加载大臣列表失败:', error)
  }
}

// 加载可用模型列表
const loadModels = async () => {
  try {
    loadingModels.value = true
    const data = await api.get('/models/available')
    // 扁平化所有提供商的模型
    availableModels.value = data.providers.flatMap(p => p.models)
  } catch (error) {
    console.error('加载模型列表失败:', error)
  } finally {
    loadingModels.value = false
  }
}

const editMinister = (minister) => {
  form.value = { ...minister }
  showAddDialog.value = true
}

const toggleMinister = async (minister) => {
  try {
    await api.put(`/ministers/${minister.id}`, {
      enabled: !minister.enabled
    })
    await loadMinisters()
  } catch (error) {
    console.error('更新大臣状态失败:', error)
  }
}

const saveMinister = async () => {
  try {
    await api.post('/ministers/', form.value)
    showAddDialog.value = false
    await loadMinisters()
  } catch (error) {
    console.error('保存大臣失败:', error)
  }
}

onMounted(() => {
  loadMinisters()
  loadModels()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.minister-card {
  padding: 10px 0;
}

.minister-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.minister-info h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.minister-actions {
  display: flex;
  gap: 10px;
}
</style>
