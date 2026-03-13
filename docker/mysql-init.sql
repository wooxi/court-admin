-- 朝廷政务管理系统数据库初始化脚本

-- 修复数据库字符集（防止中文乱码）
ALTER DATABASE court_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建大臣配置表
CREATE TABLE IF NOT EXISTS ministers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '大臣名称',
    department VARCHAR(50) NOT NULL COMMENT '所属部门',
    model_id VARCHAR(100) NOT NULL COMMENT '模型 ID',
    api_key VARCHAR(200) COMMENT 'API Key',
    workspace VARCHAR(500) NOT NULL COMMENT '工作区路径',
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_department (department),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='大臣配置表';

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(50) UNIQUE NOT NULL COMMENT '任务 ID',
    title VARCHAR(500) NOT NULL COMMENT '任务标题',
    description TEXT COMMENT '任务描述',
    creator_id INT COMMENT '创建人 ID',
    assignee_id INT NOT NULL COMMENT '承办大臣 ID',
    dispatcher_id INT COMMENT '调度大臣 ID',
    agent_session_key VARCHAR(128) NULL COMMENT '子会话标识（用于实时追踪）',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态',
    priority VARCHAR(10) DEFAULT 'medium' COMMENT '优先级',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    INDEX idx_status (status),
    INDEX idx_assignee (assignee_id),
    INDEX idx_agent_session_key (agent_session_key),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务表';

-- 创建任务流转表
CREATE TABLE IF NOT EXISTS task_flows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL COMMENT '任务 ID',
    action VARCHAR(100) NOT NULL COMMENT '动作类型',
    actor VARCHAR(50) NOT NULL COMMENT '操作人',
    details JSON COMMENT '流转详情（分派信息、执行日志等）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务流转表';

-- 创建 Token 用量表
CREATE TABLE IF NOT EXISTS token_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    minister_id INT NOT NULL COMMENT '大臣 ID',
    task_id INT COMMENT '任务 ID',
    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    total_tokens INT NOT NULL DEFAULT 0,
    cost DECIMAL(10,4) DEFAULT 0.00,
    date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_minister_id (minister_id),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Token 用量表';

-- 创建 OpenClaw 配置表
CREATE TABLE IF NOT EXISTS openclaw_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    version VARCHAR(20) NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(50),
    INDEX idx_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='OpenClaw 配置表';

-- 插入初始大臣数据
INSERT INTO ministers (name, department, model_id, workspace, enabled) VALUES
('司礼监', '司礼监', 'bailian/qwen3.5-plus', '/root/clawd', TRUE),
('兵部', '兵部', 'bailian/qwen3-coder-plus', '/root/clawd/bingbu', TRUE),
('户部', '户部', 'bailian/qwen3.5-plus', '/root/clawd/hubu', TRUE),
('礼部', '礼部', 'bailian/kimi-k2.5', '/root/clawd/libu', TRUE),
('工部', '工部', 'bailian/qwen3-coder-next', '/root/clawd/gongbu', TRUE),
('吏部', '吏部', 'bailian/qwen3.5-plus', '/root/clawd/libu2', TRUE),
('刑部', '刑部', 'bailian/qwen3-max-2026-01-23', '/root/clawd/xingbu', TRUE);
