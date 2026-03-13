-- 2026-03-13 任务实时追踪改造
-- 目标：
-- 1) 修复数据库字符集为 utf8mb4_unicode_ci
-- 2) tasks 增加 agent_session_key
-- 3) task_flows 统一为 (task_id, action, actor, details, created_at)

SET NAMES utf8mb4;

-- 1) 修复数据库字符集
ALTER DATABASE court_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2) tasks 表结构升级
ALTER TABLE tasks CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS agent_session_key VARCHAR(128) NULL COMMENT '子会话标识（用于实时追踪）' AFTER dispatcher_id;

SET @idx_exists := (
    SELECT COUNT(1)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'tasks'
      AND index_name = 'idx_agent_session_key'
);
SET @sql_idx := IF(
    @idx_exists = 0,
    'ALTER TABLE tasks ADD INDEX idx_agent_session_key (agent_session_key)',
    'SELECT "idx_agent_session_key already exists"'
);
PREPARE stmt_idx FROM @sql_idx;
EXECUTE stmt_idx;
DEALLOCATE PREPARE stmt_idx;

-- 3) task_flows 表结构升级（保留历史数据）
CREATE TABLE IF NOT EXISTS task_flows_new (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL COMMENT '任务 ID',
    action VARCHAR(100) NOT NULL COMMENT '动作类型',
    actor VARCHAR(50) NOT NULL COMMENT '操作人',
    details JSON COMMENT '流转详情（分派信息、执行日志等）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务流转表';

SET @has_legacy_columns := (
    SELECT COUNT(1)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'task_flows'
      AND column_name IN ('from_actor', 'to_actor', 'remark', 'timestamp', 'metadata')
);

SET @copy_sql := IF(
    @has_legacy_columns > 0,
    'INSERT INTO task_flows_new (id, task_id, action, actor, details, created_at)
     SELECT
       id,
       task_id,
       action,
       COALESCE(from_actor, ''system''),
       JSON_OBJECT(
         ''to_actor'', to_actor,
         ''remark'', remark,
         ''metadata'', COALESCE(metadata, JSON_OBJECT())
       ),
       COALESCE(`timestamp`, created_at, NOW())
     FROM task_flows',
    'INSERT INTO task_flows_new (id, task_id, action, actor, details, created_at)
     SELECT
       id,
       task_id,
       action,
       COALESCE(actor, ''system''),
       COALESCE(details, JSON_OBJECT()),
       COALESCE(created_at, NOW())
     FROM task_flows'
);

PREPARE stmt_copy FROM @copy_sql;
EXECUTE stmt_copy;
DEALLOCATE PREPARE stmt_copy;

-- 备份旧表并切换新表
RENAME TABLE task_flows TO task_flows_legacy_20260313, task_flows_new TO task_flows;

-- 保证自增起点正确
SET @max_id := (SELECT COALESCE(MAX(id), 0) + 1 FROM task_flows);
SET @alter_ai := CONCAT('ALTER TABLE task_flows AUTO_INCREMENT = ', @max_id);
PREPARE stmt_ai FROM @alter_ai;
EXECUTE stmt_ai;
DEALLOCATE PREPARE stmt_ai;

ALTER TABLE task_flows CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
