# Grace Doyle - Maintenance Test Suite
# Tests backend logic ONLY (CircleCI safe)

import unittest
import sqlite3
import os
from datetime import datetime

from maintenance import MaintenanceManager
import database as db_module

TEST_DB = "test_pams_maintenance.db"


# ---------------------------------------------------------
#  CREATE CLEAN TEST DATABASE
# ---------------------------------------------------------

def setup_test_db():
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # workers table (needed for get_all_workers)
    c.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

    # worker assignments table
    c.execute("""
        CREATE TABLE IF NOT EXISTS worker_assignments (
            assignment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_name    TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            request_id     INTEGER NOT NULL
        )
    """)

    # maintenance notifications table
    c.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_notifications (
            notif_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            apartment_id   INTEGER NOT NULL,
            tenant_name    TEXT NOT NULL,
            worker_name    TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            description    TEXT NOT NULL,
            created_at     TEXT NOT NULL
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

class TestMaintenanceManager(unittest.TestCase):

    def setUp(self):
        setup_test_db()
        db_module.get_connection = _test_get_connection
        self.mm = MaintenanceManager()

        # Insert mock workers
        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO workers (full_name, location) VALUES ('Alice Smith', 'Bristol')")
        c.execute("INSERT INTO workers (full_name, location) VALUES ('Bob Jones', 'London')")
        conn.commit()
        conn.close()

    def tearDown(self):
        db_module.get_connection = _original_get_connection
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # ---------------------------------------------------------
    #  WORKER AVAILABILITY
    # ---------------------------------------------------------

    def test_worker_available_initially(self):
        self.assertTrue(self.mm.is_worker_available("Alice Smith", "2026-05-01", "10:00"))

    def test_worker_not_available_after_assignment(self):
        self.mm.assign_worker("Alice Smith", "2026-05-01", "10:00", request_id=1)
        self.assertFalse(self.mm.is_worker_available("Alice Smith", "2026-05-01", "10:00"))

    def test_assign_worker_raises_if_unavailable(self):
        self.mm.assign_worker("Alice Smith", "2026-05-01", "10:00", request_id=1)
        with self.assertRaises(ValueError):
            self.mm.assign_worker("Alice Smith", "2026-05-01", "10:00", request_id=2)

    # ---------------------------------------------------------
    #  WORKER ASSIGNMENT INSERTION
    # ---------------------------------------------------------

    def test_assign_worker_inserts_row(self):
        self.mm.assign_worker("Bob Jones", "2026-06-10", "14:00", request_id=5)

        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("SELECT worker_name, scheduled_date, scheduled_time, request_id FROM worker_assignments")
        row = c.fetchone()
        conn.close()

        self.assertEqual(row, ("Bob Jones", "2026-06-10", "14:00", 5))

    # ---------------------------------------------------------
    #  NOTIFICATIONS
    # ---------------------------------------------------------

    def test_save_notification_inserts_row(self):
        self.mm.save_notification(
            apartment_id=7,
            tenant_name="John Doe",
            worker_name="Alice Smith",
            scheduled_date="2026-05-02",
            scheduled_time="09:00",
            description="Boiler repair"
        )

        conn = _test_get_connection()
        c = conn.cursor()
        c.execute("SELECT apartment_id, tenant_name, worker_name, description FROM maintenance_notifications")
        row = c.fetchone()
        conn.close()

        self.assertEqual(row, (7, "John Doe", "Alice Smith", "Boiler repair"))

    def test_get_all_notifications_returns_correct_structure(self):
        self.mm.save_notification(
            apartment_id=3,
            tenant_name="Jane Doe",
            worker_name="Bob Jones",
            scheduled_date="2026-05-03",
            scheduled_time="11:00",
            description="Window repair"
        )

        notes = self.mm.get_all_notifications()
        self.assertEqual(len(notes), 1)
        self.assertIn("apartment_id", notes[0])
        self.assertIn("tenant_name", notes[0])
        self.assertIn("worker_name", notes[0])
        self.assertIn("description", notes[0])

    # ---------------------------------------------------------
    #  WORKER FETCHING
    # ---------------------------------------------------------

    def test_get_all_workers(self):
        workers = self.mm.get_all_workers()
        self.assertEqual(len(workers), 2)
        self.assertEqual(workers[0]["full_name"], "Alice Smith")
        self.assertEqual(workers[1]["full_name"], "Bob Jones")


if __name__ == "__main__":
    unittest.main(verbosity=2)
