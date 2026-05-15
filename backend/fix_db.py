"""
修复数据库表结构，补齐所有缺失列
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'standard_review.db')
DB_PATH = os.path.abspath(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 获取当前列
cur.execute("PRAGMA table_info(review_tasks)")
existing_cols = {row[1] for row in cur.fetchall()}
print(f"现有列: {existing_cols}")

# ReviewTask 模型需要的列（参考 models/database.py）
required_cols = {
    'id', 'batch_id', 'name', 'standard_id',
    'draft_file_name', 'draft_file_path', 'draft_file_type',
    'status', 'progress', 'current_step',
    'created_at', 'completed_at', 'error_msg',
    'parsing_started_at', 'analysis_started_at',
    'score', 'critical_issues', 'major_issues', 'minor_issues'
}

missing = required_cols - existing_cols
print(f"缺失列: {missing}")

# 补齐缺失列
for col in missing:
    if col in ('batch_id', 'parsing_started_at', 'analysis_started_at',
               'score', 'critical_issues', 'major_issues', 'minor_issues'):
        col_type = 'TEXT' if col == 'batch_id' else 'TIMESTAMP' if 'time' in col else 'FLOAT' if col == 'score' else 'INTEGER'
        sql = f"ALTER TABLE review_tasks ADD COLUMN {col} {col_type}"
        try:
            cur.execute(sql)
            print(f"  + 添加 {col} ({col_type})")
        except Exception as e:
            print(f"  ! {col} 添加失败: {e}")

conn.commit()

# 验证
cur.execute("PRAGMA table_info(review_tasks)")
all_cols = {row[1] for row in cur.fetchall()}
print(f"\n补齐后: {all_cols}")

# 查一下现有任务
cur.execute("SELECT id, name, status FROM review_tasks")
print("\n现有任务:")
for row in cur.fetchall():
    print(f"  {row}")

conn.close()
print("\n完成！")
