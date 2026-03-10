<template>
  <div class="config">
    <h1>⚙️ OpenClaw 配置管理</h1>

    <!-- 配置概览 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>📄 配置概览</span>
          <div>
            <el-button type="warning" @click="createBackup">
              <el-icon><Download /></el-icon>
              备份配置
            </el-button>
            <el-button type="primary" @click="reloadConfig">
              <el-icon><Refresh /></el-icon>
              热重载
            </el-button>
          </div>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="配置文件">/root/.openclaw/openclaw.json</el-descriptions-item>
        <el-descriptions-item label="版本">{{ config.version }}</el-descriptions-item>
        <el-descriptions-item label="最后更新">{{ config.updated_at }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag type="success">✅ 正常</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 模型配置 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>🤖 可用模型列表</span>
      </template>
      
      <el-collapse>
        <el-collapse-item
          v-for="provider in models.providers"
          :key="provider.name"
          :title="provider.name"
        >
          <div class="provider-info">
            <p><strong>Base URL:</strong> {{ provider.baseUrl }}</p>
            <el-table :data="provider.models" stripe size="small">
              <el-table-column prop="id" label="模型 ID" />
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="contextWindow" label="上下文窗口" />
              <el-table-column prop="maxTokens" label="最大输出" />
              <el-table-column label="输入类型">
                <template #default="{ row }">
                  <el-tag v-for="type in row.input" :key="type" size="small">
                    {{ type }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 大臣配置 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>👥 大臣配置</span>
      </template>
      
      <el-table :data="ministers" stripe>
        <el-table-column prop="id" label="ID" width="100" />
        <el-table-column prop="name" label="名称" width="100" />
        <el-table-column prop="model.primary" label="模型" />
        <el-table-column prop="workspace" label="工作区" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editMinister(row)">编辑</el-button>
          </el-template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 备份历史 -->
    <el-card>
      <template #header>
        <span>📦 备份历史</span>
      </template>
      
      <el-table :data="backups" stripe>
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="size" label="大小">
          <template #default="{ row }">
            {{ (row.size / 1024).toFixed(2) }} KB
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary">恢复</el-button>
            <el-button size="small" type="danger">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑大臣对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑大臣配置" width="600px">
      <el-alert
        title="⚠️ 注意事项"
        type="warning"
        description="修改配置前会自动备份，修改后需要热重载才能生效。不确定的字段请勿随意修改。"
        show-icon
        style="margin-bottom: 20px;"
      />
      
      <el-form :model="editingMinister" label-width="120px">
        <el-form-item label="大臣 ID">
          <el-input v-model="editingMinister.id" disabled />
        </el-form-item>
        
        <el-form-item label="大臣名称">
          <el-input v-model="editingMinister.name" disabled />
        </el-form-item>
        
        <el-form-item label="选择模型">
          <el-select v-model="editingMinister.model.primary" placeholder="选择模型">
            <el-option
              v-for="model in allModels"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            >
              {{ model.name }} (上下文：{{ model.contextWindow }})
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="工作区">
          <el-input v-model="editingMinister.workspace" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMinisterConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const config = ref({
  version: '',
  updated_at: ''
})
const models = ref({ providers: [] })
const ministers = ref([])
const backups = ref([])
const showEditDialog = ref(false)
const editingMinister = ref({})

const allModels = computed(() => {
  return models.value.providers.flatMap(p => p.models)
})

const loadConfig = async () => {
  try {
    const data = await api.get('/config/')
    config.value = {
      version: data.version,
      updated_at: data.updated_at
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

const loadModels = async () => {
  try {
    models.value = await api.get('/models/available')
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const loadMinisters = async () => {
  try {
    const data = await api.get('/config/ministers')
    ministers.value = data.ministers
  } catch (error) {
    console.error('加载大臣配置失败:', error)
  }
}

const loadBackups = async () => {
  try {
    const data = await api.get('/config/backups')
    backups.value = data.backups
  } catch (error) {
    console.error('加载备份列表失败:', error)
  }
}

const createBackup = async () => {
  try {
    const result = await api.post('/config/backup')
    console.log('备份成功:', result)
    await loadBackups()
  } catch (error) {
    console.error('备份失败:', error)
  }
}

const reloadConfig = async () => {
  try {
    const result = await api.post('/config/reload')
    console.log('热重载:', result)
  } catch (error) {
    console.error('热重载失败:', error)
  }
}

const editMinister = (minister) => {
  editingMinister.value = JSON.parse(JSON.stringify(minister))
  showEditDialog.value = true
}

const saveMinisterConfig = async () => {
  try {
    await api.put(`/config/ministers/${editingMinister.value.id}`, {
      config_key: 'openclaw',
      config_value: {
        model: editingMinister.value.model,
        workspace: editingMinister.value.workspace
      }
    })
    showEditDialog.value = false
    await loadMinisters()
  } catch (error) {
    console.error('保存大臣配置失败:', error)
  }
}

onMounted(() => {
  loadConfig()
  loadModels()
  loadMinisters()
  loadBackups()
})
</script>

<style scoped>
.config h1 {
  margin-bottom: 20px;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.provider-info p {
  margin: 10px 0;
  color: #606266;
}
</style>
