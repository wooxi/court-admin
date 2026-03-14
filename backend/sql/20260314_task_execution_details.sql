-- 2026-03-14 任务执行明细表
-- 目标：记录任务完成时的 token 用量与耗时（仅统计启用后新数据）

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS task_execution_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL COMMENT '业务任务 ID（如 TASK-20260314-001）',
    task_pk INT NULL COMMENT 'tasks.id 主键',
    minister_id INT NOT NULL COMMENT '承办大臣 ID',
    input_tokens INT NULL COMMENT '输入 Token 数',
    output_tokens INT NULL COMMENT '输出 Token 数',
    total_tokens INT NULL COMMENT '总 Token 数',
    duration_seconds INT NULL COMMENT '任务耗时（秒）',
    completed_at DATETIME NOT NULL COMMENT '任务完成时间',
    session_key VARCHAR(128) NULL COMMENT '子会话标识',
    source VARCHAR(50) NOT NULL DEFAULT 'task_update_api' COMMENT '数据来源',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_task_execution_task_id (task_id),
    KEY idx_task_execution_minister (minister_id),
    KEY idx_task_execution_completed_at (completed_at),
    KEY idx_task_execution_session_key (session_key),
    KEY idx_task_execution_task_pk (task_pk),
    CONSTRAINT fk_task_execution_task_pk FOREIGN KEY (task_pk) REFERENCES tasks(id),
    CONSTRAINT fk_task_execution_minister FOREIGN KEY (minister_id) REFERENCES ministers(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务执行明细表';
