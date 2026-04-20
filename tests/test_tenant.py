# Grace Doyle - Tenant Management Test Suite (Corrected)
# Fully isolated, CircleCI-safe backend tests

import unittest
import sqlite3
import os
from datetime import date

import database as db_module

# ---------------------------------------------------------
#  IMPORTANT: Override DB BEFORE importing tenant functions
# ---------------------------------------------------------

TEST_DB = "tests/test_pams_tenant_mgmt.db"

def _test_get_connection():
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Override BEFORE importing the module under test
db_module.get_connection = _test_get_connection

from tenant_management import (
    edit_tenant,
    delete_tenant,
    calculate_early_termination_fee,
    check_late_payment_tenant,
    get_lease_details
)

# ---------------------------------------------------------
#  CREATE CLEAN TEST DATABASE
# ---------------------------------------------------------

def setup_test_db():
    conn = _test_get_connection()
    c = conn.cursor()

    # apartments table
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

    # tenants table
    c.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            ni_number TEXT UNIQUE,
            lease_start TEXT,
            lease_end TEXT,
            monthly_rent REAL,
            apartment_id INTEGER,
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        )
    """)

    # invoices table (needed for late payment check)
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

    conn.commit()
    conn.close()


# ---------------------------------------------------------
#  TEST SUITE
# ---------------------------------------------------------

class TestTenantManagement(unittest.TestCase):

    def setUp(self):
        # Reset DB
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        setup_test_db()

        # Insert a tenant + apartment
        conn = _test_get_connection()
        c = conn.cursor()

        c.execute("""
            INSERT INTO apartments (apartment_id, location, apt_type, monthly_rent, num_rooms, status)
            VALUES (1, 'Bristol', 'Flat', 1200, 2, 'occupied')
        """)

        c.execute("""
            INSERT INTO tenants (
                tenant_id, full_name, email, phone, ni_number,
                lease_start, lease_end, monthly_rent, apartment_id
            )
            VALUES (
                1, 'John Doe', 'john@example.com', '07123456789', 'AA123456A',
                '01-01-2026', '01-01-2027', 1200, 1
            )
        """)

        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # ---------------------------------------------------------
    #  EDIT TENANT
    # ---------------------------------------------------------

    def test_edit_tenant_updates_fields(self):
        edit_tenant(1, name="Jane Doe", email="jane@example.com")

        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("SELECT full_name, email FROM tenants WHERE tenant_id=1")
        row = c.fetchone()
        conn.close()

        self.assertEqual(row, ("Jane Doe", "jane@example.com"))

    # ---------------------------------------------------------
    #  DELETE TENANT
    # ---------------------------------------------------------

    def test_delete_tenant_removes_and_vacates_apartment(self):
        delete_tenant(1)

        conn = _test_get_connection()
        c = conn.cursor()

        c.execute("SELECT * FROM tenants WHERE tenant_id=1")
        tenant = c.fetchone()

        c.execute("SELECT tenant_id, status FROM apartments WHERE apartment_id=1")
        apt = c.fetchone()

        conn.close()

        self.assertIsNone(tenant)
        self.assertEqual(apt, (None, "vacant"))

    # ---------------------------------------------------------
    #  EARLY TERMINATION FEE
    # ---------------------------------------------------------

    def test_calculate_early_termination_fee(self):
        fee = calculate_early_termination_fee(1)
        self.assertEqual(fee, 1200 * 0.05)

    def test_calculate_early_termination_fee_no_tenant(self):
        fee = calculate_early_termination_fee(999)
        self.assertEqual(fee, 0)

    # ---------------------------------------------------------
    #  LATE PAYMENT CHECK
    # ---------------------------------------------------------

    def test_check_late_payment_tenant_true(self):
        conn = _test_get_connection()
        c = conn.cursor()

        c.execute("""
            INSERT INTO invoices (tenant_id, apartment_id, issue_date, due_date, amount, status)
            VALUES (1, 1, '01-02-2026', '10-02-2026', 1200, 'overdue')
        """)

        conn.commit()
        conn.close()

        self.assertTrue(check_late_payment_tenant(1))

    def test_check_late_payment_tenant_false(self):
        self.assertFalse(check_late_payment_tenant(1))

    # ---------------------------------------------------------
    #  GET LEASE DETAILS
    # ---------------------------------------------------------

    def test_get_lease_details(self):
        details = get_lease_details(1)

        self.assertIsNotNone(details)
        self.assertEqual(details["Monthly Rent"], 1200)
        self.assertEqual(details["Apartment ID"], 1)

    def test_get_lease_details_none(self):
        details = get_lease_details(999)
        self.assertIsNone(details)


if __name__ == "__main__":
    unittest.main(verbosity=2)
