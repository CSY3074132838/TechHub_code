import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'techhub.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Helper to update column values
def update_column(table, column, mapping):
    for old_val, new_val in mapping.items():
        c.execute(f"UPDATE {table} SET {column} = ? WHERE {column} = ?", (new_val, old_val))
        if c.rowcount > 0:
            print(f"  {table}.{column}: {old_val} -> {new_val} ({c.rowcount} rows)")

print("Migrating enum values to lowercase...")

# tasks.status
update_column('tasks', 'status', {
    'TODO': 'todo',
    'IN_PROGRESS': 'in_progress',
    'REVIEW': 'review',
    'DONE': 'done'
})

# tasks.priority
update_column('tasks', 'priority', {
    'URGENT': 'urgent',
    'HIGH': 'high',
    'MEDIUM': 'medium',
    'LOW': 'low'
})

# approvals.approval_type
update_column('approvals', 'approval_type', {
    'LEAVE': 'leave',
    'EXPENSE': 'expense',
    'PURCHASE': 'purchase',
    'OVERTIME': 'overtime',
    'PERMISSION': 'permission',
    'OTHER': 'other'
})

# approvals.status
update_column('approvals', 'status', {
    'PENDING': 'pending',
    'APPROVED': 'approved',
    'REJECTED': 'rejected',
    'CANCELLED': 'cancelled'
})

# activities.activity_type
update_column('activities', 'activity_type', {
    'TASK_CREATED': 'task_created',
    'TASK_UPDATED': 'task_updated',
    'TASK_COMPLETED': 'task_completed',
    'PROJECT_CREATED': 'project_created',
    'COMMENT_ADDED': 'comment_added',
    'APPROVAL_SUBMITTED': 'approval_submitted',
    'APPROVAL_APPROVED': 'approval_approved'
})

# clients.status
update_column('clients', 'status', {
    'POTENTIAL': 'potential',
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'LOST': 'lost'
})

# contracts.status
update_column('contracts', 'status', {
    'DRAFT': 'draft',
    'PENDING': 'pending',
    'ACTIVE': 'active',
    'COMPLETED': 'completed',
    'TERMINATED': 'terminated'
})

# tickets.status
update_column('tickets', 'status', {
    'OPEN': 'open',
    'IN_PROGRESS': 'in_progress',
    'WAITING': 'waiting',
    'RESOLVED': 'resolved',
    'CLOSED': 'closed'
})

# tickets.priority
update_column('tickets', 'priority', {
    'URGENT': 'urgent',
    'HIGH': 'high',
    'MEDIUM': 'medium',
    'LOW': 'low'
})

conn.commit()
conn.close()
print("Migration completed!")
