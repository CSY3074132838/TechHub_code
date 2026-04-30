import sqlite3
conn = sqlite3.connect('instance/techhub.db')
c = conn.cursor()

tables = ['tasks', 'approvals', 'activities', 'clients', 'contracts', 'tickets']
for t in tables:
    try:
        c.execute(f"PRAGMA table_info({t})")
        cols = c.fetchall()
        for col in cols:
            name = col[1]
            if name in ['status', 'priority', 'approval_type', 'activity_type']:
                c.execute(f'SELECT DISTINCT {name} FROM {t} WHERE {name} IS NOT NULL')
                vals = [r[0] for r in c.fetchall()]
                print(f'{t}.{name}: {vals}')
    except Exception as e:
        print(f'Error checking {t}: {e}')
conn.close()
