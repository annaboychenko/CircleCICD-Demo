# Anna Boychenko - 24030024
# Unit tests for my Apartment Management component
# used unittest which we covered in labs - it lets you run automated tests
# the brief said to test all classes so ive done that here

import unittest
import sqlite3
import os
from apartment import Apartment, MaintenanceRequest, ApartmentManager

# using a separate test database so i dont mess up the real one when testing
TEST_DB = "test_pams.db"

def setup_test_db():
    """create a fresh test database with the same tables as the real one"""
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apartments (
            apartment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            apt_type TEXT,
            monthly_rent REAL,
            num_rooms INTEGER,
            status TEXT DEFAULT 'vacant',
            tenant_id INTEGER DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            apartment_id INTEGER,
            description TEXT,
            priority TEXT,
            status TEXT DEFAULT 'open',
            date_raised TEXT,
            date_resolved TEXT,
            cost REAL,
            time_taken INTEGER,
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        )
    """)

    conn.commit()
    conn.close()


# swap out the real database connection for the test one
import apartment as apt_module
original_get_connection = apt_module.get_connection

def test_get_connection():
    conn = sqlite3.connect(TEST_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# tests for the Apartment class itself (not database stuff, just the class logic)
class TestApartmentClass(unittest.TestCase):

    # new apartment should always start as vacant
    def test_initial_status_is_vacant(self):
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        self.assertEqual(apt.status, "vacant")

    # assigning a tenant should change status to occupied and store the tenant id
    def test_assign_tenant(self):
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        apt.assign_tenant(101)
        self.assertEqual(apt.status, "occupied")
        self.assertEqual(apt.tenant_id, 101)

    # removing a tenant should set status back to vacant and tenant_id back to None
    def test_remove_tenant(self):
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2, "occupied", 101)
        apt.remove_tenant()
        self.assertEqual(apt.status, "vacant")
        self.assertIsNone(apt.tenant_id)

    # just checking the str method works and includes the location
    def test_str_representation(self):
        apt = Apartment(1, "Bristol", "2-bedroom flat", 1200.00, 2)
        self.assertIn("Bristol", str(apt))


# tests for the MaintenanceRequest class
class TestMaintenanceRequestClass(unittest.TestCase):

    # new requests should always be open
    def test_initial_status_is_open(self):
        req = MaintenanceRequest(1, 1, "Broken boiler", "high")
        self.assertEqual(req.status, "open")

    # resolving should update status, cost and time taken
    def test_resolve_request(self):
        req = MaintenanceRequest(1, 1, "Broken boiler", "high")
        req.resolve(150.00, 3)
        self.assertEqual(req.status, "resolved")
        self.assertEqual(req.cost, 150.00)
        self.assertEqual(req.time_taken, 3)


# tests for ApartmentManager - this tests the actual database operations
class TestApartmentManager(unittest.TestCase):

    # runs before each test - sets up a clean test db
    def setUp(self):
        setup_test_db()
        apt_module.get_connection = test_get_connection  # swap to test db

    # runs after each test - deletes the test db so each test starts fresh
    def tearDown(self):
        apt_module.get_connection = original_get_connection
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # basic test - add an apartment and check it shows up
    def test_add_apartment(self):
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        self.assertEqual(len(apartments), 1)
        self.assertEqual(apartments[0].location, "Bristol")

    # should raise ValueError if rent is negative
    def test_add_apartment_invalid_rent(self):
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.add_apartment("Bristol", "2-bedroom flat", -100, 2)

    # should raise ValueError if location is empty
    def test_add_apartment_empty_location(self):
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.add_apartment("", "2-bedroom flat", 1200.00, 2)

    # assign tenant and check the status and tenant id updated in the db
    def test_assign_tenant(self):
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        apt_id = apartments[0].apartment_id
        manager.assign_tenant(apt_id, 101)
        updated = manager.get_apartment_by_id(apt_id)
        self.assertEqual(updated.status, "occupied")
        self.assertEqual(updated.tenant_id, 101)

    # shouldnt be able to assign a second tenant to an occupied apartment
    def test_assign_tenant_to_occupied_apartment(self):
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        apt_id = apartments[0].apartment_id
        manager.assign_tenant(apt_id, 101)
        with self.assertRaises(ValueError):
            manager.assign_tenant(apt_id, 102)  # this should fail

    # remove tenant and check it goes back to vacant
    def test_remove_tenant(self):
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        apt_id = apartments[0].apartment_id
        manager.assign_tenant(apt_id, 101)
        manager.remove_tenant(apt_id)
        updated = manager.get_apartment_by_id(apt_id)
        self.assertEqual(updated.status, "vacant")
        self.assertIsNone(updated.tenant_id)

    # add a maintenance request and check it saved correctly
    def test_add_maintenance_request(self):
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        apt_id = apartments[0].apartment_id
        manager.add_maintenance_request(apt_id, "Broken boiler", "high")
        requests = manager.get_all_maintenance_requests()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].priority, "high")

    # invalid priority should be rejected
    def test_add_maintenance_invalid_priority(self):
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        apt_id = apartments[0].apartment_id
        with self.assertRaises(ValueError):
            manager.add_maintenance_request(apt_id, "Broken boiler", "urgent")  # not a valid priority

    # resolve a request and check status, cost and time updated
    def test_resolve_maintenance_request(self):
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        apt_id = apartments[0].apartment_id
        manager.add_maintenance_request(apt_id, "Broken boiler", "high")
        requests = manager.get_all_maintenance_requests()
        req_id = requests[0].request_id
        manager.resolve_maintenance_request(req_id, 150.00, 3)
        updated = manager.get_all_maintenance_requests()
        self.assertEqual(updated[0].status, "resolved")
        self.assertEqual(updated[0].cost, 150.00)

    # negative cost should be rejected
    def test_resolve_maintenance_negative_cost(self):
        manager = ApartmentManager()
        with self.assertRaises(ValueError):
            manager.resolve_maintenance_request(1, -50, 2)

    # delete an apartment and check its gone
    def test_delete_apartment(self):
        manager = ApartmentManager()
        manager.add_apartment("Bristol", "2-bedroom flat", 1200.00, 2)
        apartments = manager.get_all_apartments()
        apt_id = apartments[0].apartment_id
        manager.delete_apartment(apt_id)
        self.assertEqual(len(manager.get_all_apartments()), 0)


# run the tests when this file is executed directly
if __name__ == "__main__":
    unittest.main(verbosity=2)