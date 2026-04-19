# Hamna Khan - [23032525]
# maintenance.py - maintenance component for PAMS
#
# handles the full maintenance lifecycle:
#   - worker scheduling and availability checking (persisted to DB)
#   - tenant notifications when a maintenance visit is scheduled
#   - fetching workers from the database (not hardcoded)
#
# tables created by this file:
#   - worker_assignments: stores which worker is booked on which date/time
#   - maintenance_notifications: logs all communications sent to tenants

from database import get_connection
from datetime import datetime


class MaintenanceManager:
    def __init__(self):
        # ensure our tables exist every time the app starts
        self._ensure_tables()

    def _ensure_tables(self):
        # creates the worker_assignments and maintenance_notifications tables
        # if they dont exist yet - called on startup so schema is always ready
        conn = get_connection()
        c = conn.cursor()

        # stores worker bookings - used to check availability across sessions
        # without this, availability resets every time the app restarts
        c.execute("""
            CREATE TABLE IF NOT EXISTS worker_assignments (
                assignment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_name    TEXT    NOT NULL,
                scheduled_date TEXT    NOT NULL,
                scheduled_time TEXT    NOT NULL,
                request_id     INTEGER NOT NULL
            )
        """)

        # stores all tenant notifications sent when a maintenance visit is scheduled
        # shown in the notifications tab in the sidebar
        c.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_notifications (
                notif_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                apartment_id   INTEGER NOT NULL,
                tenant_name    TEXT    NOT NULL,
                worker_name    TEXT    NOT NULL,
                scheduled_date TEXT    NOT NULL,
                scheduled_time TEXT    NOT NULL,
                description    TEXT    NOT NULL,
                created_at     TEXT    NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def is_worker_available(self, worker, date, time):
        # checks the worker_assignments table to see if the worker already
        # has a booking at the given date and time
        # returns True if available, False if already booked
        # persisted to DB so checks survive app restarts
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM worker_assignments
            WHERE worker_name = ? AND scheduled_date = ? AND scheduled_time = ?
        """, (worker, date, time))
        count = c.fetchone()[0]
        conn.close()
        # count == 0 means no existing booking at this slot so worker is free
        return count == 0

    def assign_worker(self, worker, date, time, request_id):
        # saves a worker assignment to the database
        # checks availability first - raises ValueError if the slot is taken
        # persisting to DB means the booking survives app restarts
        if not self.is_worker_available(worker, date, time):
            raise ValueError("Worker not available at this date and time.")
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO worker_assignments
                (worker_name, scheduled_date, scheduled_time, request_id)
            VALUES (?, ?, ?, ?)
        """, (worker, date, time, request_id))
        conn.commit()
        conn.close()

    def save_notification(self, apartment_id, tenant_name,
                          worker_name, scheduled_date, scheduled_time, description):
        # saves a tenant notification to the maintenance_notifications table
        # called automatically when a new maintenance request is submitted
        # in a real system this would trigger an email/sms via an api like twilio
        # here we store it and display it in the notifications tab
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO maintenance_notifications
                (apartment_id, tenant_name, worker_name,
                 scheduled_date, scheduled_time, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (apartment_id, tenant_name, worker_name,
              scheduled_date, scheduled_time, description,
              datetime.now().strftime("%d-%m-%Y %H:%M")))
        conn.commit()
        conn.close()

    def get_all_notifications(self):
        # retrieves all tenant notifications from the DB, newest first
        # used by show_notifications() in apartment_gui.py
        # wrapped in try/except in case the table doesnt exist yet
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("""
                SELECT apartment_id, tenant_name, worker_name,
                       scheduled_date, scheduled_time, description, created_at
                FROM   maintenance_notifications
                ORDER  BY notif_id DESC
            """)
            rows = c.fetchall()
        except Exception:
            rows = []
        conn.close()
        cols = ["apartment_id", "tenant_name", "worker_name",
                "scheduled_date", "scheduled_time", "description", "created_at"]
        return [dict(zip(cols, r)) for r in rows]

    def get_all_workers(self):
        # fetches all maintenance workers from the workers table in the DB
        # workers stored in database with their location so the dropdown
        # in the new request form always reflects the current staff list
        # replaced the original hardcoded list of names which was not scalable
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT worker_id, full_name, location FROM workers ORDER BY location, full_name"
        )
        rows = c.fetchall()
        conn.close()
        return [{"worker_id": r[0], "full_name": r[1], "location": r[2]} for r in rows]