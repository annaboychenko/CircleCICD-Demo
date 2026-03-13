# Anna Boychenko - 24030024
# Apartment Management Component - PAMS group project
# this is my part of the group project, im handling apartment management
# which covers registering apartments, assigning tenants and dealing with maintenance requests

import sqlite3
from database import get_connection
from datetime import date

# class to represent a single apartment
# i used a class here because we learned in lectures that OOP is better for
# organising data like this rather than just using dictionaries or lists
class Apartment:

    # this sets up all the info for one apartment when its created
    # status is vacant by default because new apartments wont have tenants yet
    # tenant_id is None by default for the same reason
    def __init__(self, apartment_id, location, apt_type, monthly_rent, num_rooms, status="vacant", tenant_id=None):
        self.apartment_id = apartment_id
        self.location = location
        self.apt_type = apt_type      # e.g. 1-bedroom flat, studio, 3-bedroom house
        self.monthly_rent = monthly_rent
        self.num_rooms = num_rooms
        self.status = status          # vacant or occupied
        self.tenant_id = tenant_id    # None if nobody lives there

    # called when a tenant moves in - updates the status and saves their id
    def assign_tenant(self, tenant_id):
        self.tenant_id = tenant_id
        self.status = "occupied"

    # called when a tenant moves out - clears tenant and resets to vacant
    def remove_tenant(self):
        self.tenant_id = None
        self.status = "vacant"

    # useful for debugging so i can print apartment info easily
    def __str__(self):
        return f"Apartment {self.apartment_id} - {self.location} ({self.apt_type}) - {self.status}"


# class for maintenance requests - when something breaks in an apartment
# the brief said we need to track the whole lifecycle from raised to resolved
class MaintenanceRequest:

    # all the info needed for a maintenance request
    # date_raised auto sets to today if you dont pass one in
    # cost and time_taken start as None because we dont know them until its fixed
    def __init__(self, request_id, apartment_id, description, priority, status="open",
                 date_raised=None, date_resolved=None, cost=None, time_taken=None):
        self.request_id = request_id
        self.apartment_id = apartment_id   # which apartment has the problem
        self.description = description     # what the actual issue is
        self.priority = priority           # low, medium or high
        self.status = status               # open or resolved
        self.date_raised = date_raised or str(date.today())  # defaults to today
        self.date_resolved = date_resolved  # filled in when fixed
        self.cost = cost                    # how much the repair cost
        self.time_taken = time_taken        # how long it took in hours

    # maintenance staff call this when the issue is fixed
    # updates the status and records cost, time taken and todays date
    def resolve(self, cost, time_taken):
        self.status = "resolved"
        self.cost = cost
        self.time_taken = time_taken
        self.date_resolved = str(date.today())

    def __str__(self):
        return f"Request {self.request_id} - Apartment {self.apartment_id} - {self.priority} priority - {self.status}"


# this class handles all the database operations for my component
# i kept it separate from the Apartment class so the actual data isnt mixed up with the db logic
# this makes testing easier too because i can test the logic without needing the gui running
class ApartmentManager:

    # adds a new apartment to the database
    # i added validation so that rubbish data cant get saved - the brief mentioned data integrity
    def add_apartment(self, location, apt_type, monthly_rent, num_rooms):
        # check inputs before doing anything with the database
        if not location or not apt_type:
            raise ValueError("Location and type cannot be empty")
        if monthly_rent <= 0:
            raise ValueError("Monthly rent must be greater than 0")
        if num_rooms <= 0:
            raise ValueError("Number of rooms must be greater than 0")

        conn = get_connection()
        cursor = conn.cursor()   # need a cursor to actually run sql
        cursor.execute("""
            INSERT INTO apartments (location, apt_type, monthly_rent, num_rooms, status)
            VALUES (?, ?, ?, ?, 'vacant')
        """, (location, apt_type, monthly_rent, num_rooms))
        conn.commit()    # have to commit or changes wont actually save
        conn.close()

    # returns all apartments from the database as a list of Apartment objects
    def get_all_apartments(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apartments")
        rows = cursor.fetchall()   # fetchall gets every row as a list of tuples
        conn.close()
        # convert each tuple row into an Apartment object
        # *row unpacks the tuple so each value goes into the right parameter
        return [Apartment(*row) for row in rows]

    # get just one apartment using its id - needed when editing or checking status
    def get_apartment_by_id(self, apartment_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apartments WHERE apartment_id = ?", (apartment_id,))
        row = cursor.fetchone()   # fetchone just gets one row
        conn.close()
        if row:
            return Apartment(*row)
        return None   # return None rather than crashing if not found

    # update apartment details - used when admin edits an apartment
    def update_apartment(self, apartment_id, location, apt_type, monthly_rent, num_rooms):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE apartments
            SET location = ?, apt_type = ?, monthly_rent = ?, num_rooms = ?
            WHERE apartment_id = ?
        """, (location, apt_type, monthly_rent, num_rooms, apartment_id))
        conn.commit()
        conn.close()

    # delete an apartment but only if there are no open maintenance requests on it
    # didnt want someone to delete an apartment that still has unresolved issues
    def delete_apartment(self, apartment_id):
        conn = get_connection()
        cursor = conn.cursor()
        # check for open requests first before deleting
        cursor.execute("""
            SELECT COUNT(*) FROM maintenance_requests
            WHERE apartment_id = ? AND status = 'open'
        """, (apartment_id,))
        open_requests = cursor.fetchone()[0]
        if open_requests > 0:
            conn.close()
            raise ValueError("Cannot delete apartment with open maintenance requests")
        cursor.execute("DELETE FROM apartments WHERE apartment_id = ?", (apartment_id,))
        conn.commit()
        conn.close()

    # assign a tenant to an apartment - checks its actually vacant before doing it
    def assign_tenant(self, apartment_id, tenant_id):
        conn = get_connection()
        cursor = conn.cursor()
        # first check the apartment exists and isnt already taken
        cursor.execute("SELECT status FROM apartments WHERE apartment_id = ?", (apartment_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError("Apartment not found")
        if row[0] == "occupied":
            conn.close()
            raise ValueError("Apartment is already occupied")
        # update both fields at the same time
        cursor.execute("""
            UPDATE apartments SET status = 'occupied', tenant_id = ?
            WHERE apartment_id = ?
        """, (tenant_id, apartment_id))
        conn.commit()
        conn.close()

    # remove tenant - sets tenant_id back to null and status back to vacant
    def remove_tenant(self, apartment_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE apartments SET status = 'vacant', tenant_id = NULL
            WHERE apartment_id = ?
        """, (apartment_id,))
        conn.commit()
        conn.close()

    # add a new maintenance request for an apartment
    # only allows low medium or high as priority values
    def add_maintenance_request(self, apartment_id, description, priority):
        if not description:
            raise ValueError("Description cannot be empty")
        if priority not in ["low", "medium", "high"]:
            raise ValueError("Priority must be low, medium or high")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_requests (apartment_id, description, priority, status, date_raised)
            VALUES (?, ?, ?, 'open', ?)
        """, (apartment_id, description, priority, str(date.today())))
        conn.commit()
        conn.close()

    # get all maintenance requests from the database
    def get_all_maintenance_requests(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maintenance_requests")
        rows = cursor.fetchall()
        conn.close()
        return [MaintenanceRequest(*row) for row in rows]

    # mark a maintenance request as resolved
    # maintenance staff enter cost and time after fixing the issue
    def resolve_maintenance_request(self, request_id, cost, time_taken):
        if cost < 0:
            raise ValueError("Cost cannot be negative")
        if time_taken <= 0:
            raise ValueError("Time taken must be greater than 0")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE maintenance_requests
            SET status = 'resolved', cost = ?, time_taken = ?, date_resolved = ?
            WHERE request_id = ?
        """, (cost, time_taken, str(date.today()), request_id))
        conn.commit()
        conn.close()

    # adds fake data for testing and demo purposes
    # the brief said to fill with mock data so the system looks realistic
    def insert_mock_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        # only add mock data if the table is empty - dont want duplicates
        cursor.execute("SELECT COUNT(*) FROM apartments")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        # example apartments in the uk cities mentioned in the brief
        apartments = [
            ("Bristol", "2-bedroom flat", 1200.00, 2),
            ("Bristol", "1-bedroom flat", 850.00, 1),
            ("London", "3-bedroom house", 2500.00, 3),
            ("London", "Studio", 950.00, 1),
            ("Manchester", "2-bedroom flat", 1100.00, 2),
            ("Cardiff", "1-bedroom flat", 750.00, 1),
        ]

        # executemany lets you insert multiple rows at once which is cleaner
        cursor.executemany("""
            INSERT INTO apartments (location, apt_type, monthly_rent, num_rooms, status)
            VALUES (?, ?, ?, ?, 'vacant')
        """, apartments)

        # some example maintenance requests to show in the demo
        maintenance = [
            (1, "Broken boiler", "high"),
            (2, "Leaking tap", "low"),
            (3, "Faulty electrics", "high"),
        ]

        for apt_id, desc, priority in maintenance:
            cursor.execute("""
                INSERT INTO maintenance_requests (apartment_id, description, priority, status, date_raised)
                VALUES (?, ?, ?, 'open', ?)
            """, (apt_id, desc, priority, str(date.today())))

        conn.commit()
        conn.close()
        print("mock data added ok")