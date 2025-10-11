-- 创建数据库（如果还没有）
CREATE DATABASE IF NOT EXISTS ai_chat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE ai_chat;

-- 创建 subject 表（对话主题）
CREATE TABLE subject (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL COMMENT '主题标题',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建 chatcontent 表（聊天消息）
CREATE TABLE chatcontent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subjectid INT NOT NULL COMMENT '关联主题ID',
    content TEXT NOT NULL COMMENT '消息内容（支持[附件]标记）',
    role ENUM('user', 'assistant') NOT NULL COMMENT '角色：用户或AI助手',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (subjectid) REFERENCES subject(id) ON DELETE CASCADE,
    INDEX idx_subjectid (subjectid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 显示表结构确认
SHOW TABLES;
DESCRIBE subject;
DESCRIBE chatcontent;