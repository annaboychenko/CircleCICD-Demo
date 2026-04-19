from database import get_connection

conn = get_connection()
cursor = conn.cursor()

# Get real tenants that are already assigned to apartments
cursor.execute("""
    SELECT tenant_id, apartment_id, monthly_rent
    FROM tenants
    WHERE apartment_id IS NOT NULL
    ORDER BY tenant_id
    LIMIT 3
""")
rows = cursor.fetchall()

if len(rows) < 3:
    print("Not enough tenants linked to apartments. Need at least 3.")
    conn.close()
    raise SystemExit

t1, a1, r1 = rows[0]
t2, a2, r2 = rows[1]
t3, a3, r3 = rows[2]

# Delete old finance demo data safely
cursor.execute("DELETE FROM payments")
cursor.execute("DELETE FROM invoices")

# Insert invoices using real IDs
cursor.execute("""
    INSERT INTO invoices (tenant_id, apartment_id, issue_date, due_date, amount, status)
    VALUES (?, ?, '2026-04-01', '2026-04-10', ?, 'paid')
""", (t1, a1, r1 or 1200.0))

invoice1 = cursor.lastrowid

cursor.execute("""
    INSERT INTO invoices (tenant_id, apartment_id, issue_date, due_date, amount, status)
    VALUES (?, ?, '2026-04-01', '2026-04-10', ?, 'unpaid')
""", (t2, a2, r2 or 2500.0))

cursor.execute("""
    INSERT INTO invoices (tenant_id, apartment_id, issue_date, due_date, amount, status)
    VALUES (?, ?, '2026-04-01', '2026-03-10', ?, 'overdue')
""", (t3, a3, r3 or 1100.0))

# Insert one payment linked to invoice1
cursor.execute("""
    INSERT INTO payments (tenant_id, apartment_id, invoice_id, amount, due_date, paid_date, status)
    VALUES (?, ?, ?, ?, '2026-04-10', '2026-04-05', 'paid')
""", (t1, a1, invoice1, r1 or 1200.0))

conn.commit()
conn.close()

print("Finance mock data added successfully.")