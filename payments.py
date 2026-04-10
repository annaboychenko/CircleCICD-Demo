import sqlite3
from database import get_connection
from datetime import date


class FinanceManager:

    # ---------------------------------------------------------
#  INVOICE CREATION
# ---------------------------------------------------------

    def create_invoice(self, tenant_id, apartment_id, amount, due_date):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO invoices (tenant_id, apartment_id, issue_date, due_date, amount)
            VALUES (?, ?, date('now'), ?, ?)
        """, (tenant_id, apartment_id, due_date, amount))

        invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return invoice_id


    # ---------------------------------------------------------
    #  CREATE PENDING PAYMENT (linked to invoice)
    # ---------------------------------------------------------

    def create_pending_payment(self, invoice_id, tenant_id, apartment_id, amount, due_date):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO payments (tenant_id, apartment_id, invoice_id, amount, due_date, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (tenant_id, apartment_id, invoice_id, amount, due_date))

        conn.commit()
        conn.close()




    # ---------------------------------------------------------
    #  GET UPDATED INVOICES (for Record Payment page)
    # ---------------------------------------------------------


    def update_overdue_invoices(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE invoices
            SET status = 'overdue'
            WHERE status = 'unpaid'
            AND due_date < DATE('now')
        """)

        conn.commit()
        conn.close()

    # ---------------------------------------------------------
    #  GET ALL INVOICES (for Payments Overview page)
    # ---------------------------------------------------------

    def get_all_invoices(self):
        self.update_overdue_invoices()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT i.invoice_id, i.amount, i.due_date, i.status,
                t.full_name, t.tenant_id, i.apartment_id
            FROM invoices i
            JOIN tenants t ON i.tenant_id = t.tenant_id
            ORDER BY i.invoice_id DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        invoices = []
        for r in rows:
            invoices.append({
                "invoice_id": r[0],
                "amount": r[1],
                "due_date": r[2],
                "status": r[3],
                "tenant_name": r[4],
                "tenant_id": r[5],
                "apartment_id": r[6]
            })

        return invoices


    # ---------------------------------------------------------
    #  GET UNPAID INVOICES (for Record Payment page)
    # ---------------------------------------------------------

    def get_unpaid_invoices(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT i.invoice_id, i.amount, i.due_date, i.status,
                t.full_name, t.tenant_id, i.apartment_id
            FROM invoices i
            JOIN tenants t ON i.tenant_id = t.tenant_id
            WHERE i.status = 'unpaid'
            ORDER BY i.due_date ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        invoices = []
        for r in rows:
            invoices.append({
                "invoice_id": r[0],
                "amount": r[1],
                "due_date": r[2],
                "status": r[3],
                "tenant_name": r[4],
                "tenant_id": r[5],
                "apartment_id": r[6]
            })

        return invoices
    




    


    # ---------------------------------------------------------
    #  GET ACTIVE TENANTS (for Generate Invoice page)
    # ---------------------------------------------------------

    def get_active_tenants(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tenant_id, full_name, apartment_id
            FROM tenants
            WHERE apartment_id IS NOT NULL
        """)

        rows = cursor.fetchall()
        conn.close()

        tenants = []
        for r in rows:
            tenants.append({
                "tenant_id": r[0],
                "full_name": r[1],
                "apartment_id": r[2]
            })

        return tenants


    # ---------------------------------------------------------
    #  MARK PAYMENT AS PAID
    # ---------------------------------------------------------

    def mark_payment_as_paid(self, invoice_id):
        conn = get_connection()
        cursor = conn.cursor()

        # update payment
        cursor.execute("""
            UPDATE payments
            SET paid_date = date('now'), status = 'paid'
            WHERE invoice_id = ?
        """, (invoice_id,))

        # update invoice
        cursor.execute("""
            UPDATE invoices
            SET status = 'paid'
            WHERE invoice_id = ?
        """, (invoice_id,))

        conn.commit()
        conn.close()


    # ---------------------------------------------------------
    #  GENERATE RECEIPT
    # ---------------------------------------------------------

    def generate_receipt(self, invoice_id):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.payment_id, p.amount, p.paid_date,
                t.full_name, a.location, i.invoice_id
            FROM payments p
            JOIN tenants t ON p.tenant_id = t.tenant_id
            JOIN apartments a ON p.apartment_id = a.apartment_id
            JOIN invoices i ON p.invoice_id = i.invoice_id
            WHERE p.invoice_id = ?
        """, (invoice_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "payment_id": row[0],
            "amount": row[1],
            "paid_date": row[2],
            "tenant": row[3],
            "apartment": row[4],
            "invoice_id": row[5]
        }