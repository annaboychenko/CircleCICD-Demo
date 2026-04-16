from database import get_connection

conn = get_connection()
cursor = conn.cursor()

# clear old demo finance data if needed
cursor.execute("DELETE FROM payments")
cursor.execute("DELETE FROM invoices")

# sample invoices
cursor.execute("""
INSERT INTO invoices (tenant_id, apartment_id, issue_date, due_date, amount, status)
VALUES
(1, 1, '2026-04-01', '2026-04-10', 1200.00, 'paid'),
(2, 4, '2026-04-01', '2026-04-10', 2500.00, 'unpaid'),
(3, 7, '2026-04-01', '2026-03-10', 1100.00, 'overdue')
""")

# sample payments linked to invoice 1
cursor.execute("""
INSERT INTO payments (tenant_id, apartment_id, invoice_id, amount, due_date, paid_date, status)
VALUES
(1, 1, 1, 1200.00, '2026-04-10', '2026-04-05', 'paid')
""")

conn.commit()
conn.close()

print("Finance mock data added successfully.")