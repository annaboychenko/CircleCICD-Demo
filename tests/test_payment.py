# Grace Doyle - Payments Test Suite
# Tests backend logic ONLY (CircleCI safe)

import unittest
import sqlite3
import os
from datetime import date, timedelta

from payments import FinanceManager
import database as db_module

TEST_DB = "test_pams_payments.db"


# ---------------------------------------------------------
#  CREATE CLEAN TEST DATABASE
# ---------------------------------------------------------

def setup_test_db():
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # apartments
    c.execute("""
        CREATE TABLE IF NOT EXISTS apartments (
            apartment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            apt_type TEXT NOT NULL,
            monthly_rent REAL NOT NULL,
            num_rooms INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'vacant',
            tenant_id INTEGER DEFAULT NULL
        )
    """)

    # tenants
    c.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            ni_number TEXT UNIQUE,
            apartment_id INTEGER,
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        )
    """)

    # invoices
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            apartment_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'unpaid',
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        )
    """)

    # payments
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            apartment_id INTEGER NOT NULL,
            invoice_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            paid_date TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id),
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
        )
    """)

    # notifications
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Override get_connection to use test DB
_original_get_connection = db_module.get_connection

def _test_get_connection():
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------
#  TEST SUITE
# ---------------------------------------------------------

class TestFinanceManager(unittest.TestCase):

    def setUp(self):
        setup_test_db()
        db_module.get_connection = _test_get_connection
        self.fm = FinanceManager()

        # Insert a tenant + apartment for testing
        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO apartments (location, apt_type, monthly_rent, num_rooms) VALUES ('Bristol','Flat',1200,2)")
        c.execute("INSERT INTO tenants (full_name, ni_number, apartment_id) VALUES ('John Doe','AA123456A',1)")
        conn.commit()
        conn.close()

    def tearDown(self):
        db_module.get_connection = _original_get_connection
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # ---------------------------------------------------------
    #  INVOICE CREATION
    # ---------------------------------------------------------

    def test_create_invoice(self):
        invoice_id = self.fm.create_invoice(1, 1, 1200, "01-05-2026")
        self.assertIsNotNone(invoice_id)

        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("SELECT amount FROM invoices WHERE invoice_id=?", (invoice_id,))
        row = c.fetchone()
        conn.close()

        self.assertEqual(row[0], 1200)

    # ---------------------------------------------------------
    #  PENDING PAYMENT CREATION
    # ---------------------------------------------------------

    def test_create_pending_payment(self):
        invoice_id = self.fm.create_invoice(1, 1, 1200, "01-05-2026")
        self.fm.create_pending_payment(invoice_id, 1, 1, 1200, "01-05-2026")

        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("SELECT status FROM payments WHERE invoice_id=?", (invoice_id,))
        row = c.fetchone()
        conn.close()

        self.assertEqual(row[0], "pending")

    # ---------------------------------------------------------
    #  OVERDUE INVOICE UPDATE
    # ---------------------------------------------------------

    def test_update_overdue_invoices(self):
        # Create invoice with yesterday's date
        yesterday = (date.today() - timedelta(days=1)).strftime("%d-%m-%Y")
        self.fm.create_invoice(1, 1, 1200, yesterday)

        self.fm.update_overdue_invoices()

        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("SELECT status FROM invoices")
        status = c.fetchone()[0]
        conn.close()

        self.assertEqual(status, "overdue")

    # ---------------------------------------------------------
    #  GET ALL INVOICES
    # ---------------------------------------------------------

    def test_get_all_invoices(self):
        self.fm.create_invoice(1, 1, 1200, "01-05-2026")
        invoices = self.fm.get_all_invoices()
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0]["tenant_name"], "John Doe")

    # ---------------------------------------------------------
    #  GET UNPAID INVOICES
    # ---------------------------------------------------------

    def test_get_unpaid_invoices(self):
        self.fm.create_invoice(1, 1, 1200, "01-05-2026")
        unpaid = self.fm.get_unpaid_invoices()
        self.assertEqual(len(unpaid), 1)

    # ---------------------------------------------------------
    #  GET ACTIVE TENANTS
    # ---------------------------------------------------------

    def test_get_active_tenants(self):
        tenants = self.fm.get_active_tenants()
        self.assertEqual(len(tenants), 1)
        self.assertEqual(tenants[0]["full_name"], "John Doe")

    # ---------------------------------------------------------
    #  MARK PAYMENT AS PAID
    # ---------------------------------------------------------

    def test_mark_payment_as_paid(self):
        invoice_id = self.fm.create_invoice(1, 1, 1200, "01-05-2026")
        self.fm.create_pending_payment(invoice_id, 1, 1, 1200, "01-05-2026")

        self.fm.mark_payment_as_paid(invoice_id)

        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("SELECT status FROM payments WHERE invoice_id=?", (invoice_id,))
        status = c.fetchone()[0]
        conn.close()

        self.assertIn("paid", status)

    # ---------------------------------------------------------
    #  GET PAYMENT ID
    # ---------------------------------------------------------

    def test_get_payment_id_by_invoice(self):
        invoice_id = self.fm.create_invoice(1, 1, 1200, "01-05-2026")
        self.fm.create_pending_payment(invoice_id, 1, 1, 1200, "01-05-2026")

        pid = self.fm.get_payment_id_by_invoice(invoice_id)
        self.assertIsNotNone(pid)

    # ---------------------------------------------------------
    #  GENERATE RECEIPT
    # ---------------------------------------------------------

    def test_generate_receipt(self):
        invoice_id = self.fm.create_invoice(1, 1, 1200, "01-05-2026")
        self.fm.create_pending_payment(invoice_id, 1, 1, 1200, "01-05-2026")
        self.fm.mark_payment_as_paid(invoice_id)

        receipt = self.fm.generate_receipt(invoice_id)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["tenant"], "John Doe")


if __name__ == "__main__":
    unittest.main(verbosity=2)
