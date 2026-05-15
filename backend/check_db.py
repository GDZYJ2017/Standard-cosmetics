import sqlite3
conn = sqlite3.connect('../data/standard_review.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(review_tasks)")
print("=== review_tasks columns ===")
for row in cur.fetchall():
    print(row)

cur.execute("SELECT id, name, status FROM review_tasks LIMIT 5")
print("\n=== existing tasks ===")
for row in cur.fetchall():
    print(row)

conn.close()
print("\nDone.")
