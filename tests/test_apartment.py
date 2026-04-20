# Anna Boychenko - 24030024
# unit tests for the apartment management component
# using unittest which we covered in labs - lets you run automated tests
# the brief says to test all classes and cover invalid/edge case inputs
# i used a separate test database so the real data never gets touched

import unittest
import sqlite3
import os
from apartmentAndTenant import Apartment, MaintenanceRequest, ApartmentManager

# separate test db so real data is never touched during testing
TEST_DB = "test_pams.db"


def setup_test_db():
    """create a clean test database with the same schema as the real one"""
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # apartments table - matches database.py schema exactly
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apartments (
            apartment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            location       TEXT    NOT NULL,
            apt_type       TEXT    NOT NULL,
            monthly_rent   REAL    NOT NULL,
            num_rooms      INTEGER NOT NULL,
            status         TEXT    NOT NULL DEFAULT 'vacant',
            tenant_id      INTEGER DEFAULT NULL
        )
    """)

    # maintenance requests table - matches database.py schema exactly
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_requests (
            request_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            apartment_id   INTEGER NOT NULL,
            description    TEXT    NOT NULL,
            priority       TEXT    NOT NULL DEFAULT 'low',
            status         TEXT    NOT NULL DEFAULT 'open',
            date_raised    TEXT    NOT NULL,
            date_resolved  TEXT    DEFAULT NULL,
            cost           REAL    DEFAULT NULL,
            time_taken     INTEGER DEFAULT NULL,
            resolution_notes TEXT DEFAULT NULL,
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        )
    """)

    # users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL DEFAULT 'front_desk',
            location   TEXT    DEFAULT NULL,
            full_name  TEXT    DEFAULT NULL,
            email      TEXT    DEFAULT NULL
        )
    """)

    # tenants table 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            location        TEXT    DEFAULT NULL,
            full_name       TEXT    NOT NULL,
            email           TEXT    NOT NULL,
            phone           TEXT    NOT NULL,
            ni_number       TEXT    NOT NULL UNIQUE,
            occupation      TEXT    DEFAULT NULL,
            tenant_references      TEXT    DEFAULT NULL,
            apartment_id    INTEGER DEFAULT NULL,
            lease_period    TEXT    DEFAULT NULL,
            lease_start     TEXT    DEFAULT NULL,
            lease_end       TEXT    DEFAULT NULL,
            deposit_amount  REAL    DEFAULT NULL,
            monthly_rent    REAL    DEFAULT NULL,
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        )
    """)

    # invoice table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id      INTEGER NOT NULL,
            apartment_id   INTEGER NOT NULL,
            issue_date     TEXT NOT NULL,
            due_date       TEXT NOT NULL,
            amount         REAL NOT NULL,
            status         TEXT NOT NULL DEFAULT 'unpaid',
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        )
    """)

    # payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id      INTEGER NOT NULL,
            apartment_id   INTEGER NOT NULL,
            invoice_id INTEGER NOT NULL,
            amount         REAL    NOT NULL,
            due_date       TEXT    NOT NULL,
            paid_date      TEXT    DEFAULT NULL,
            status         TEXT    NOT NULL DEFAULT 'pending',
            FOREIGN KEY (tenant_id)   REFERENCES tenants(tenant_id),
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id),
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
        )
    """)

    #notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    #workers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            location  TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# swap get_connection in the apartment module to use the test db instead
import apartmentAndTenant as apt_module
_original_get_connection = apt_module.get_connection


def _test_get_connection():
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ======================================================================= #
#  APARTMENT CLASS TESTS (no db needed - testing the object itself)       #
# ======================================================================= #

class TestApartmentClass(unittest.TestCase):

    def test_default_status_is_vacant(self):
        """new apartment should always start as vacant"""
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        self.assertEqual(apt.status, "vacant")

    def test_default_tenant_id_is_none(self):
        """tenant_id should be None when no tenant is assigned yet"""
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        self.assertIsNone(apt.tenant_id)

    def test_assign_tenant_changes_status(self):
        """assigning a tenant should set status to occupied"""
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        apt.assign_tenant(101)
        self.assertEqual(apt.status, "occupied")

    def test_assign_tenant_stores_id(self):
        """assigning a tenant should store their id on the object"""
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        apt.assign_tenant(101)
        self.assertEqual(apt.tenant_id, 101)

    def test_remove_tenant_resets_status(self):
        """removing a tenant should set status back to vacant"""
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2, "occupied", 101)
        apt.remove_tenant()
        self.assertEqual(apt.status, "vacant")

    def test_remove_tenant_clears_tenant_id(self):
        """removing a tenant should set tenant_id back to None"""
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2, "occupied", 101)
        apt.remove_tenant()
        self.assertIsNone(apt.tenant_id)

    def test_str_contains_location(self):
        """str output should include the apartment location"""
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        self.assertIn("Bristol", str(apt))

    def test_str_contains_status(self):
        """str output should include the current status"""
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        self.assertIn("vacant", str(apt))


# ======================================================================= #
#  MAINTENANCE REQUEST CLASS TESTS                                         #
# ======================================================================= #

class TestMaintenanceRequestClass(unittest.TestCase):

    def test_default_status_is_open(self):
        """new maintenance requests should always start as open"""
        req = MaintenanceRequest(1, 1, "broken boiler", "high")
        self.assertEqual(req.status, "open")

    def test_default_date_raised_set(self):
        """date_raised should default to todays date if not provided"""
        from datetime import date
        req = MaintenanceRequest(1, 1, "broken boiler", "high")
        self.assertEqual(req.date_raised, str(date.today()))

    def test_resolve_sets_status(self):
        """resolving a request should set status to resolved"""
        req = MaintenanceRequest(1, 1, "broken boiler", "high")
        req.resolve(150.00, 3)
        self.assertEqual(req.status, "resolved")

    def test_resolve_stores_cost(self):
        """resolving should store the cost on the object"""
        req = MaintenanceRequest(1, 1, "broken boiler", "high")
        req.resolve(150.00, 3)
        self.assertEqual(req.cost, 150.00)

    def test_resolve_stores_time_taken(self):
        """resolving should store the time taken on the object"""
        req = MaintenanceRequest(1, 1, "broken boiler", "high")
        req.resolve(150.00, 3)
        self.assertEqual(req.time_taken, 3)

    def test_resolve_sets_date_resolved(self):
        """resolving should set date_resolved to todays date"""
        from datetime import date
        req = MaintenanceRequest(1, 1, "broken boiler", "high")
        req.resolve(150.00, 3)
        self.assertEqual(req.date_resolved, str(date.today()))

    def test_str_contains_priority(self):
        """str output should include the priority level"""
        req = MaintenanceRequest(1, 1, "broken boiler", "high")
        self.assertIn("high", str(req))


# ======================================================================= #
#  APARTMENT MANAGER TESTS (database operations)                          #
# ======================================================================= #

class TestApartmentManager(unittest.TestCase):

    def setUp(self):
        """runs before each test - fresh test db every time"""
        setup_test_db()
        apt_module.get_connection = _test_get_connection

    def tearDown(self):
        """runs after each test - delete test db so next test starts clean"""
        apt_module.get_connection = _original_get_connection
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # ------------------------------------------------------------------ #
    #  ADD APARTMENT                                                      #
    # ------------------------------------------------------------------ #

    def test_add_apartment_saves_to_db(self):
        """adding an apartment should persist it to the database"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        self.assertEqual(len(apartments), 1)

    def test_add_apartment_correct_location(self):
        """saved apartment should have the correct location"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        self.assertEqual(manager.get_all_apartments()[0].location, "Bristol")

    def test_add_apartment_starts_vacant(self):
        """newly added apartment should be vacant by default"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        self.assertEqual(manager.get_all_apartments()[0].status, "vacant")

    def test_add_apartment_rejects_zero_rent(self):
        """rent of 0 should raise ValueError"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.add_apartment("Bristol", "2-bedroom flat", 0, 2)

    def test_add_apartment_rejects_negative_rent(self):
        """negative rent should raise ValueError"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.add_apartment("Bristol", "2-bedroom flat", -100, 2)

    def test_add_apartment_rejects_empty_location(self):
        """empty location string should raise ValueError"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.add_apartment("", "2-bedroom flat", 1200.00, 2)

    def test_add_apartment_rejects_zero_rooms(self):
        """zero rooms should raise ValueError"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 0)

    def test_add_apartment_rejects_empty_type(self):
        """empty apartment type should raise ValueError"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.add_apartment("Bristol", "", 1200.00, 2)

    # ------------------------------------------------------------------ #
    #  GET APARTMENT                                                      #
    # ------------------------------------------------------------------ #

    def test_get_apartment_by_id_returns_correct(self):
        """should return the right apartment when searching by id"""
        manager = ApartmentManager()
        manager.add_apartment("London", "Studio", 950.00, 1)
        apt_id = manager.get_all_apartments()[0].apartment_id
        found  = manager.get_apartment_by_id(apt_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.location, "London")

    def test_get_apartment_by_id_returns_none_if_missing(self):
        """should return None for an id that doesnt exist"""
        manager = ApartmentManager()
        result = manager.get_apartment_by_id(9999)
        self.assertIsNone(result)

    def test_get_apartments_by_location(self):
        """should filter apartments correctly by city"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol",    "Studio",         700.00, 1)
        manager.add_apartment("Manchester", "1-bedroom flat", 780.00, 1)
        results = manager.get_apartments_by_location("Bristol")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].location, "Bristol")

    # ------------------------------------------------------------------ #
    #  UPDATE APARTMENT                                                   #
    # ------------------------------------------------------------------ #

    def test_update_apartment_changes_rent(self):
        """update should save the new rent to the database"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.update_apartment(apt_id, "Bristol", "2-bedroom flat", 1350.00, 2)
        updated = manager.get_apartment_by_id(apt_id)
        self.assertEqual(updated.monthly_rent, 1350.00)

    def test_update_apartment_rejects_invalid_rent(self):
        """update with zero rent should raise ValueError"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        with self.assertRaises(ValueError):
            manager.update_apartment(apt_id, "Bristol", "2-bedroom flat", 0, 2)

    # ------------------------------------------------------------------ #
    #  ASSIGN / REMOVE TENANT                                             #
    # ------------------------------------------------------------------ #

    def test_assign_tenant_changes_status_in_db(self):
        """assigning a tenant should update status to occupied in the db"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.assign_tenant(
            tenant_id=101,
            apartment_id=apt_id,
            lease_period="12 months",
            lease_start="01-01-2025",
            lease_end="01-01-2026"
        )     
        updated = manager.get_apartment_by_id(apt_id)
        self.assertEqual(updated.status, "occupied")

    def test_assign_tenant_stores_tenant_id_in_db(self):
        """assigning a tenant should save their id in the db"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.assign_tenant(
            tenant_id=101,
            apartment_id=apt_id,
            lease_period="12 months",
            lease_start="01-01-2025",
            lease_end="01-01-2026"
        )       
        updated = manager.get_apartment_by_id(apt_id)
        self.assertEqual(updated.tenant_id, 101)

    def test_assign_tenant_to_occupied_raises_error(self):
        """assigning a second tenant to an occupied apartment should fail"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.assign_tenant(
            tenant_id=101,
            apartment_id=apt_id,
            lease_period="12 months",
            lease_start="01-01-2025",
            lease_end="01-01-2026"
        )        
        with self.assertRaises(ValueError):
            manager.assign_tenant(
                tenant_id=202,
                apartment_id=apt_id,
                lease_period="12 months",
                lease_start="01-01-2025",
                lease_end="01-01-2026"
            )

    def test_assign_tenant_to_nonexistent_apartment_raises_error(self):
        """assigning a tenant to a missing apartment id should fail"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.assign_tenant(
                tenant_id=101,
                apartment_id=9999,
                lease_period="12 months",
                lease_start="01-01-2025",
                lease_end="01-01-2026"
            )

    def test_remove_tenant_resets_to_vacant_in_db(self):
        """removing a tenant should set status back to vacant in the db"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.assign_tenant(
            tenant_id=101,
            apartment_id=apt_id,
            lease_period="12 months",
            lease_start="01-01-2025",
            lease_end="01-01-2026"
        )           
        manager.remove_tenant(apt_id)
        updated = manager.get_apartment_by_id(apt_id)
        self.assertEqual(updated.status, "vacant")
        self.assertIsNone(updated.tenant_id)

    # ------------------------------------------------------------------ #
    #  DELETE APARTMENT                                                   #
    # ------------------------------------------------------------------ #

    def test_delete_apartment_removes_from_db(self):
        """deleted apartment should no longer appear in get_all_apartments"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.delete_apartment(apt_id)
        self.assertEqual(len(manager.get_all_apartments()), 0)

    def test_delete_apartment_blocked_if_open_requests(self):
        """deleting an apartment with open maintenance requests should fail"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.add_maintenance_request(apt_id, "broken boiler", "high")
        with self.assertRaises(ValueError):
            manager.delete_apartment(apt_id)

    # ------------------------------------------------------------------ #
    #  MAINTENANCE REQUESTS                                               #
    # ------------------------------------------------------------------ #

    def test_add_maintenance_request_saves_to_db(self):
        """maintenance request should appear in get_all_maintenance_requests"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.add_maintenance_request(apt_id, "broken boiler", "high")
        requests = manager.get_all_maintenance_requests()
        self.assertEqual(len(requests), 1)

    def test_add_maintenance_request_correct_priority(self):
        """saved request should have the priority that was passed in"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.add_maintenance_request(apt_id, "broken boiler", "high")
        self.assertEqual(manager.get_all_maintenance_requests()[0].priority, "High")


    def test_add_maintenance_request_invalid_priority_raises_error(self):
        """priority values outside low/medium/high should raise ValueError"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        with self.assertRaises(ValueError):
            manager.add_maintenance_request(apt_id, "broken boiler", "urgent")

    def test_add_maintenance_request_empty_description_raises_error(self):
        """empty description should raise ValueError"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id = manager.get_all_apartments()[0].apartment_id
        with self.assertRaises(ValueError):
            manager.add_maintenance_request(apt_id, "", "high")

    def test_add_maintenance_request_nonexistent_apartment_raises_error(self):
        """adding a request for a missing apartment id should fail"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.add_maintenance_request(9999, "broken boiler", "high")

    def test_resolve_maintenance_request_changes_status(self):
        """resolved request should have status 'resolved' in the db"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id  = manager.get_all_apartments()[0].apartment_id
        manager.add_maintenance_request(apt_id, "broken boiler", "high")
        req_id  = manager.get_all_maintenance_requests()[0].request_id
        manager.resolve_maintenance_request(req_id, 150.00, 3)
        updated = manager.get_all_maintenance_requests()[0]
        self.assertEqual(updated.status, "resolved")

    def test_resolve_maintenance_request_stores_cost(self):
        """resolved request should have the correct cost saved"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id  = manager.get_all_apartments()[0].apartment_id
        manager.add_maintenance_request(apt_id, "broken boiler", "high")
        req_id  = manager.get_all_maintenance_requests()[0].request_id
        manager.resolve_maintenance_request(req_id, 150.00, 3)
        self.assertEqual(manager.get_all_maintenance_requests()[0].cost, 150.00)

    def test_resolve_maintenance_negative_cost_raises_error(self):
        """negative cost should raise ValueError"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.resolve_maintenance_request(1, -50, 2)

    def test_resolve_maintenance_zero_time_raises_error(self):
        """zero time taken should raise ValueError"""
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.resolve_maintenance_request(1, 50.00, 0)

    def test_get_requests_by_apartment(self):
        """should only return requests for the specified apartment"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol",    "2-bedroom flat", 1200.00, 2)
        manager.add_apartment("Manchester", "1-bedroom flat",  780.00, 1)
        apt1 = manager.get_all_apartments()[0].apartment_id
        apt2 = manager.get_all_apartments()[1].apartment_id
        manager.add_maintenance_request(apt1, "broken boiler",  "high")
        manager.add_maintenance_request(apt2, "leaking tap",    "low")
        results = manager.get_requests_by_apartment(apt1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].apartment_id, apt1)

    # ------------------------------------------------------------------ #
    #  REPORTING HELPERS                                                  #
    # ------------------------------------------------------------------ #

    def test_occupancy_summary_correct_counts(self):
        """summary should correctly count total, occupied and vacant"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        manager.add_apartment("London",  "Studio",          950.00, 1)
        apt_id = manager.get_all_apartments()[0].apartment_id
        manager.assign_tenant(
            tenant_id=101,
            apartment_id=apt_id,
            lease_period="12 months",
            lease_start="01-01-2025",
            lease_end="01-01-2026"
        )        
        summary = manager.get_occupancy_summary()
        self.assertEqual(summary["total"],    2)
        self.assertEqual(summary["occupied"], 1)
        self.assertEqual(summary["vacant"],   1)

    def test_occupancy_summary_empty(self):
        """occupancy rate should be 0.0 when there are no apartments"""
        manager  = ApartmentManager()
        summary  = manager.get_occupancy_summary()
        self.assertEqual(summary["rate"], 0.0)

    def test_maintenance_cost_summary(self):
        """cost summary should sum only resolved request costs"""
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apt_id  = manager.get_all_apartments()[0].apartment_id
        manager.add_maintenance_request(apt_id, "broken boiler", "high")
        req_id  = manager.get_all_maintenance_requests()[0].request_id
        manager.resolve_maintenance_request(req_id, 200.00, 2)
        summary = manager.get_maintenance_cost_summary()
        self.assertEqual(summary["total_cost"], 200.00)
        self.assertEqual(summary["resolved"],   1)


# run with: python test_apartment.py
if __name__ == "__main__":
    unittest.main(verbosity=2)