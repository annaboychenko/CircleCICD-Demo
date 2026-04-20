# Grace Doyle - Reporting Test Suite (Corrected)
# Fully isolated, CircleCI-safe backend tests

import unittest
import sqlite3
import os

import database as db_module

# ---------------------------------------------------------
#  IMPORTANT: Override DB BEFORE importing ReportManager
# ---------------------------------------------------------

TEST_DB = "tests/test_pams_reporting.db"

def _test_get_connection():
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

db_module.get_connection = _test_get_connection

from reporting import ReportManager


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

    # invoices table
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            apartment_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'unpaid'
        )
    """)

    # maintenance requests table
    c.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            apartment_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            cost REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
#  TEST SUITE
# ---------------------------------------------------------

class TestReporting(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        setup_test_db()
        self.rm = ReportManager()

        conn = _test_get_connection()
        c = conn.cursor()

        # Insert apartments
        c.execute("""
            INSERT INTO apartments (apartment_id, location, apt_type, monthly_rent, num_rooms, status)
            VALUES (1, 'Bristol', 'Flat', 1200, 2, 'occupied')
        """)
        c.execute("""
            INSERT INTO apartments (apartment_id, location, apt_type, monthly_rent, num_rooms, status)
            VALUES (2, 'Bristol', 'Studio', 900, 1, 'vacant')
        """)
        c.execute("""
            INSERT INTO apartments (apartment_id, location, apt_type, monthly_rent, num_rooms, status)
            VALUES (3, 'London', 'Flat', 1500, 2, 'occupied')
        """)

        # Insert invoices
        c.execute("""
            INSERT INTO invoices (tenant_id, apartment_id, issue_date, due_date, amount, status)
            VALUES (1, 1, '01-01-2026', '10-01-2026', 1200, 'paid')
        """)
        c.execute("""
            INSERT INTO invoices (tenant_id, apartment_id, issue_date, due_date, amount, status)
            VALUES (2, 3, '01-01-2026', '10-01-2026', 1500, 'overdue')
        """)

        # Insert maintenance requests
        c.execute("""
            INSERT INTO maintenance_requests (apartment_id, description, status, cost)
            VALUES (1, 'Boiler fix', 'resolved', 200)
        """)
        c.execute("""
            INSERT INTO maintenance_requests (apartment_id, description, status, cost)
            VALUES (3, 'Window repair', 'open', 0)
        """)

        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # ---------------------------------------------------------
    #  OCCUPANCY BY CITY
    # ---------------------------------------------------------

    def test_get_occupancy_by_city(self):
        results = self.rm.get_occupancy_by_city()

        self.assertEqual(len(results), 2)

        bristol = next(r for r in results if r["location"] == "Bristol")
        self.assertEqual(bristol["total_apartments"], 2)
        self.assertEqual(bristol["occupied"], 1)
        self.assertEqual(bristol["vacant"], 1)
        self.assertEqual(bristol["occupancy_rate"], 50.0)

    # ---------------------------------------------------------
    #  OCCUPANCY BY APARTMENT
    # ---------------------------------------------------------

    def test_get_occupancy_by_apartment(self):
        results = self.rm.get_occupancy_by_apartment()
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["apartment_id"], 1)

    # ---------------------------------------------------------
    #  OCCUPANCY FOR CITY
    # ---------------------------------------------------------

    def test_get_occupancy_for_city(self):
        result = self.rm.get_occupancy_for_city("Bristol")
        self.assertEqual(result["occupied"], 1)
        self.assertEqual(result["vacant"], 1)
        self.assertEqual(result["occupancy_rate"], 50.0)

    def test_get_occupancy_for_city_none(self):
        result = self.rm.get_occupancy_for_city("Manchester")
        self.assertEqual(result["total_apartments"], 0)

    # ---------------------------------------------------------
    #  FINANCIAL SUMMARY
    # ---------------------------------------------------------

    def test_get_financial_summary(self):
        summary = self.rm.get_financial_summary()

        self.assertEqual(summary["total_invoices"], 2)
        self.assertEqual(summary["total_billed"], 2700)
        self.assertEqual(summary["collected_rent"], 1200)
        self.assertEqual(summary["pending_rent"], 0)
        self.assertEqual(summary["overdue_rent"], 1500)
        self.assertEqual(summary["collection_rate"], round((1200/2700)*100, 2))

    # ---------------------------------------------------------
    #  MAINTENANCE SUMMARY
    # ---------------------------------------------------------

    def test_get_maintenance_summary(self):
        summary = self.rm.get_maintenance_summary()

        self.assertEqual(summary["total_requests"], 2)
        self.assertEqual(summary["resolved_requests"], 1)
        self.assertEqual(summary["open_requests"], 1)
        self.assertEqual(summary["total_maintenance_cost"], 200)

    # ---------------------------------------------------------
    #  MAINTENANCE COSTS BY CITY
    # ---------------------------------------------------------

    def test_get_maintenance_costs_by_city(self):
        results = self.rm.get_maintenance_costs_by_city()

        bristol = next(r for r in results if r["location"] == "Bristol")
        self.assertEqual(bristol["total_requests"], 1)
        self.assertEqual(bristol["total_cost"], 200)

    # ---------------------------------------------------------
    #  MAINTENANCE COSTS FOR CITY
    # ---------------------------------------------------------

    def test_get_maintenance_costs_for_city(self):
        result = self.rm.get_maintenance_costs_for_city("Bristol")
        self.assertEqual(result["total_requests"], 1)
        self.assertEqual(result["total_cost"], 200)

    def test_get_maintenance_costs_for_city_none(self):
        result = self.rm.get_maintenance_costs_for_city("Manchester")
        self.assertEqual(result["total_requests"], 0)

    # ---------------------------------------------------------
    #  MAINTENANCE COSTS FOR APARTMENT
    # ---------------------------------------------------------

    def test_get_maintenance_costs_for_apartment(self):
        result = self.rm.get_maintenance_costs_for_apartment(1)
        self.assertEqual(result["total_requests"], 1)
        self.assertEqual(result["total_cost"], 200)

    def test_get_maintenance_costs_for_apartment_none(self):
        result = self.rm.get_maintenance_costs_for_apartment(999)
        self.assertEqual(result["total_requests"], 0)

    # ---------------------------------------------------------
    #  FULL REPORT
    # ---------------------------------------------------------

    def test_generate_full_report(self):
        report = self.rm.generate_full_report()

        self.assertIn("occupancy_by_city", report)
        self.assertIn("financial_summary", report)
        self.assertIn("maintenance_summary", report)
        self.assertIn("maintenance_costs_by_city", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
