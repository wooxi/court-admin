-- 2026-03-13 任务追踪结构统一
-- 目标：
-- 1) tasks 增加 agent_session_key
-- 2) task_flows 统一到 from_actor/to_actor/remark/metadata/created_at

SET NAMES utf8mb4;

ALTER DATABASE court_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- tasks：补充实时追踪字段
ALTER TABLE tasks CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE tasks
  ADD COLUMN IF NOT EXISTS agent_session_key VARCHAR(128) NULL COMMENT '子会话标识（用于实时追踪）' AFTER dispatcher_id;

SET @idx_task_session := (
  SELECT COUNT(1)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'tasks'
    AND index_name = 'idx_agent_session_key'
);
SET @sql_task_session := IF(
  @idx_task_session = 0,
  'ALTER TABLE tasks ADD INDEX idx_agent_session_key (agent_session_key)',
  'SELECT "idx_agent_session_key exists"'
);
PREPARE stmt_task_session FROM @sql_task_session;
EXECUTE stmt_task_session;
DEALLOCATE PREPARE stmt_task_session;

-- task_flows：若不存在则创建新结构
CREATE TABLE IF NOT EXISTS task_flows (
  id INT AUTO_INCREMENT PRIMARY KEY,
  task_id INT NOT NULL COMMENT '任务 ID',
  from_actor VARCHAR(50) NOT NULL COMMENT '发起方',
  to_actor VARCHAR(50) NOT NULL COMMENT '接收方',
  action VARCHAR(100) NOT NULL COMMENT '动作类型',
  remark TEXT NULL COMMENT '备注',
  metadata JSON NULL COMMENT '扩展元数据',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_task_id (task_id),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务流转表';

ALTER TABLE task_flows CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 兼容旧结构：补字段
ALTER TABLE task_flows
  ADD COLUMN IF NOT EXISTS from_actor VARCHAR(50) NULL COMMENT '发起方' AFTER task_id,
  ADD COLUMN IF NOT EXISTS to_actor VARCHAR(50) NULL COMMENT '接收方' AFTER from_actor,
  ADD COLUMN IF NOT EXISTS remark TEXT NULL COMMENT '备注' AFTER action,
  ADD COLUMN IF NOT EXISTS metadata JSON NULL COMMENT '扩展元数据' AFTER remark,
  ADD COLUMN IF NOT EXISTS created_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP AFTER metadata;

-- 从 legacy actor/details 迁移数据（如果存在）
SET @has_actor := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'task_flows' AND column_name = 'actor'
);

SET @sql_migrate_actor := IF(
  @has_actor > 0,
  'UPDATE task_flows
     SET from_actor = COALESCE(from_actor, actor, "system")
   WHERE from_actor IS NULL OR from_actor = ""',
  'SELECT "actor column not found"'
);
PREPARE stmt_migrate_actor FROM @sql_migrate_actor;
EXECUTE stmt_migrate_actor;
DEALLOCATE PREPARE stmt_migrate_actor;

SET @has_details := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'task_flows' AND column_name = 'details'
);

-- 仅在 details 存在时执行兼容迁移
SET @sql_migrate_details := IF(
  @has_details > 0,
  'UPDATE task_flows
     SET to_actor = COALESCE(to_actor, JSON_UNQUOTE(JSON_EXTRACT(details, ''$.to_actor'')), ''system''),
         remark = COALESCE(remark, JSON_UNQUOTE(JSON_EXTRACT(details, ''$.remark''))),
         metadata = COALESCE(metadata, JSON_EXTRACT(details, ''$.metadata''), details)
   WHERE to_actor IS NULL OR remark IS NULL OR metadata IS NULL',
  'SELECT "details column not found"'
);
PREPARE stmt_migrate_details FROM @sql_migrate_details;
EXECUTE stmt_migrate_details;
DEALLOCATE PREPARE stmt_migrate_details;

-- 若旧表用 timestamp 字段，回填到 created_at
SET @has_timestamp := (
  SELECT COUNT(1)
  FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'task_flows' AND column_name = 'timestamp'
);
SET @sql_migrate_time := IF(
  @has_timestamp > 0,
  'UPDATE task_flows
     SET created_at = COALESCE(created_at, `timestamp`)
   WHERE created_at IS NULL',
  'SELECT "timestamp column not found"'
);
PREPARE stmt_migrate_time FROM @sql_migrate_time;
EXECUTE stmt_migrate_time;
DEALLOCATE PREPARE stmt_migrate_time;

-- 兜底默认值
UPDATE task_flows SET from_actor = 'system' WHERE from_actor IS NULL OR from_actor = '';
UPDATE task_flows SET to_actor = 'system' WHERE to_actor IS NULL OR to_actor = '';
UPDATE task_flows SET metadata = JSON_OBJECT() WHERE metadata IS NULL;
UPDATE task_flows SET created_at = NOW() WHERE created_at IS NULL;

ALTER TABLE task_flows
  MODIFY COLUMN from_actor VARCHAR(50) NOT NULL,
  MODIFY COLUMN to_actor VARCHAR(50) NOT NULL,
  MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
