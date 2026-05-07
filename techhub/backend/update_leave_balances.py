"""
更新假期余额默认值
- 年假(annual): 10天
- 病假(sick): 15天
- 事假(personal): 7天
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'techhub.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 更新各类假期总天数
updates = [
    ('annual', 10, '年假'),
    ('sick', 15, '病假'),
    ('personal', 7, '事假'),
]

for leave_type, days, name in updates:
    cursor.execute(
        "UPDATE leave_balances SET total_days = ? WHERE leave_type = ?",
        (days, leave_type)
    )
    affected = cursor.rowcount
    print(f"{name}({leave_type}): 更新了 {affected} 条记录 → 总天数 {days} 天")

conn.commit()
conn.close()
print("\n更新完成，刷新页面即可看到新数据。")
