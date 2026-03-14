-- court-admin 初始化脚本（与当前代码模型保持一致）

CREATE DATABASE IF NOT EXISTS court_admin
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE court_admin;

-- 大臣配置表
CREATE TABLE IF NOT EXISTS ministers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL COMMENT '大臣名称（如司礼监）',
  department VARCHAR(50) NOT NULL COMMENT '所属部门',
  model_id VARCHAR(100) NOT NULL COMMENT '模型 ID',
  api_key VARCHAR(200) COMMENT 'API Key（可加密存储）',
  workspace VARCHAR(500) NOT NULL COMMENT '工作区路径',
  enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_name (name),
  INDEX idx_department (department)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
  id INT PRIMARY KEY AUTO_INCREMENT,
  task_id VARCHAR(50) UNIQUE NOT NULL COMMENT '业务任务 ID（如 TASK-20260314-001）',
  title VARCHAR(500) NOT NULL COMMENT '任务标题',
  description TEXT COMMENT '任务描述',
  creator_id INT COMMENT '创建人 ID',
  assignee_id INT NOT NULL COMMENT '承办大臣 ID',
  dispatcher_id INT COMMENT '调度大臣 ID（司礼监）',
  agent_session_key VARCHAR(128) COMMENT '子会话标识',
  status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/processing/completed',
  priority VARCHAR(10) DEFAULT 'medium' COMMENT 'high/medium/low',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  INDEX idx_task_id (task_id),
  INDEX idx_status (status),
  INDEX idx_assignee (assignee_id),
  INDEX idx_dispatcher (dispatcher_id),
  INDEX idx_created_at (created_at),
  INDEX idx_agent_session_key (agent_session_key),
  CONSTRAINT fk_tasks_creator FOREIGN KEY (creator_id) REFERENCES ministers(id),
  CONSTRAINT fk_tasks_assignee FOREIGN KEY (assignee_id) REFERENCES ministers(id),
  CONSTRAINT fk_tasks_dispatcher FOREIGN KEY (dispatcher_id) REFERENCES ministers(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 任务流转表
CREATE TABLE IF NOT EXISTS task_flows (
  id INT PRIMARY KEY AUTO_INCREMENT,
  task_id INT NOT NULL COMMENT '任务主键 ID',
  from_actor VARCHAR(50) NOT NULL COMMENT '发起方',
  to_actor VARCHAR(50) NOT NULL COMMENT '接收方',
  action VARCHAR(100) NOT NULL COMMENT '动作类型',
  remark TEXT NULL COMMENT '备注',
  metadata JSON NULL COMMENT '扩展元数据',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  INDEX idx_task_id (task_id),
  INDEX idx_created_at (created_at),
  CONSTRAINT fk_task_flows_task_id FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 任务执行明细（TOKEN/耗时）
CREATE TABLE IF NOT EXISTS task_execution_details (
  id INT PRIMARY KEY AUTO_INCREMENT,
  task_id VARCHAR(50) NOT NULL UNIQUE COMMENT '业务任务 ID',
  task_pk INT NULL COMMENT 'tasks 主键 ID',
  minister_id INT NOT NULL COMMENT '承办大臣 ID',
  input_tokens INT NULL,
  output_tokens INT NULL,
  total_tokens INT NULL,
  duration_seconds INT NULL,
  completed_at TIMESTAMP NOT NULL COMMENT '完成时间',
  session_key VARCHAR(128) NULL,
  source VARCHAR(50) NOT NULL DEFAULT 'task_update_api',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_minister_id (minister_id),
  INDEX idx_task_pk (task_pk),
  INDEX idx_completed_at (completed_at),
  INDEX idx_session_key (session_key),
  CONSTRAINT fk_task_exec_minister FOREIGN KEY (minister_id) REFERENCES ministers(id),
  CONSTRAINT fk_task_exec_task_pk FOREIGN KEY (task_pk) REFERENCES tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Token 用量表（兼容保留）
CREATE TABLE IF NOT EXISTS token_usage (
  id INT PRIMARY KEY AUTO_INCREMENT,
  minister_id INT NOT NULL,
  task_id INT,
  input_tokens INT DEFAULT 0,
  output_tokens INT DEFAULT 0,
  total_tokens INT DEFAULT 0,
  cost DECIMAL(10, 4) DEFAULT 0.0000,
  date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_minister_id (minister_id),
  INDEX idx_task_id (task_id),
  INDEX idx_date (date),
  CONSTRAINT fk_token_usage_minister FOREIGN KEY (minister_id) REFERENCES ministers(id),
  CONSTRAINT fk_token_usage_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- OpenClaw 配置表
CREATE TABLE IF NOT EXISTS openclaw_config (
  id INT PRIMARY KEY AUTO_INCREMENT,
  config_key VARCHAR(100) UNIQUE NOT NULL,
  config_value TEXT NOT NULL,
  version VARCHAR(20) NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  updated_by VARCHAR(50),
  INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 默认大臣配置（存在则跳过）
INSERT IGNORE INTO ministers (id, name, department, model_id, workspace, enabled) VALUES
(1, '司礼监', '调度层', 'qwen3-coder-plus', '/root/clawd/silijian', TRUE),
(2, '兵部', '执行层', 'qwen3-coder-plus', '/root/clawd/bingbu', TRUE),
(3, '户部', '执行层', 'qwen3.5-plus', '/root/clawd/hubu', TRUE),
(4, '礼部', '执行层', 'qwen3.5-plus', '/root/clawd/libu', TRUE),
(5, '工部', '执行层', 'qwen3-coder-plus', '/root/clawd/gongbu', TRUE),
(6, '吏部', '执行层', 'qwen3.5-plus', '/root/clawd/libu2', TRUE),
(7, '刑部', '执行层', 'qwen3.5-plus', '/root/clawd/xingbu', TRUE);

-- 默认配置
INSERT IGNORE INTO openclaw_config (config_key, config_value, version, updated_by) VALUES
('system', '{"name":"朝廷政务系统"}', '1.0.0', 'system');
