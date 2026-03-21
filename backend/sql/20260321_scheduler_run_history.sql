-- 2026-03-21 scheduler_run_history 持久化
-- 目标：将定时任务执行记录落库，支持分页查询与统计分析

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS scheduler_run_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(128) NOT NULL COMMENT '定时任务 ID',
    task_name VARCHAR(255) NULL COMMENT '定时任务名称',
    started_at DATETIME NOT NULL COMMENT '开始时间',
    ended_at DATETIME NULL COMMENT '结束时间',
    duration_ms INT NULL COMMENT '耗时（毫秒）',
    status VARCHAR(32) NOT NULL DEFAULT 'unknown' COMMENT '执行状态',
    result TEXT NULL COMMENT '执行结果摘要',
    source VARCHAR(64) NOT NULL DEFAULT 'scheduler_overview' COMMENT '数据来源',
    raw_payload JSON NULL COMMENT '原始数据快照',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_scheduler_run_task_start (task_id, started_at),
    KEY idx_scheduler_run_started_at (started_at),
    KEY idx_scheduler_run_status (status),
    KEY idx_scheduler_run_task_status (task_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时任务运行历史';
