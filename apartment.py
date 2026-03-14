# Anna Boychenko - 24030024
# Apartment Management Component - PAMS group project
# this is my part of the group project - i handle apartment management
# which covers registering apartments, assigning tenants, and managing maintenance requests
#
# HOW OTHER COMPONENTS INTEGRATE WITH THIS:
#   - tenant management team: call assign_tenant(apt_id, tenant_id) after creating a tenant
#     and remove_tenant(apt_id) when a tenant leaves. tenant_id comes from their tenants table
#   - maintenance staff team: use get_all_maintenance_requests() to read open requests
#     and resolve_maintenance_request() to mark them done after logging their work
#   - reporting team: use get_all_apartments() and get_all_maintenance_requests()
#     to pull the data you need for occupancy and cost reports
#   - payment team: monthly_rent is stored on each apartment - pull it via get_apartment_by_id()

import sqlite3
from database import get_connection
from datetime import date


# ----------------------------------------------------------------------- #
#  APARTMENT CLASS                                                         #
# ----------------------------------------------------------------------- #

class Apartment:
    """represents a single apartment property in the system"""

    def __init__(self, apartment_id, location, apt_type, monthly_rent,
                 num_rooms, status="vacant", tenant_id=None):
        self.apartment_id = apartment_id
        self.location     = location
        self.apt_type     = apt_type         # e.g. 1-bedroom flat, studio, 3-bedroom house
        self.monthly_rent = monthly_rent
        self.num_rooms    = num_rooms
        self.status       = status           # 'vacant' or 'occupied'
        self.tenant_id    = tenant_id        # None if nobody lives there yet

    def assign_tenant(self, tenant_id):
        """called when a tenant moves in - updates status and stores their id"""
        self.tenant_id = tenant_id
        self.status = "occupied"

    def remove_tenant(self):
        """called when a tenant moves out - clears tenant and resets to vacant"""
        self.tenant_id = None
        self.status = "vacant"

    def __str__(self):
        return (f"Apartment {self.apartment_id} — {self.location} "
                f"({self.apt_type}) — {self.status}")


# ----------------------------------------------------------------------- #
#  MAINTENANCE REQUEST CLASS                                               #
# ----------------------------------------------------------------------- #

class MaintenanceRequest:
    """
    represents a single maintenance issue raised for an apartment
    lifecycle: open → (maintenance staff investigates) → resolved
    """

    def __init__(self, request_id, apartment_id, description, priority,
                 status="open", date_raised=None, date_resolved=None,
                 cost=None, time_taken=None):
        self.request_id   = request_id
        self.apartment_id = apartment_id    # which apartment has the problem
        self.description  = description     # what the actual issue is
        self.priority     = priority        # 'low', 'medium', or 'high'
        self.status       = status          # 'open' or 'resolved'
        self.date_raised  = date_raised or str(date.today())
        self.date_resolved = date_resolved  # filled in when fixed
        self.cost         = cost            # repair cost in £
        self.time_taken   = time_taken      # hours taken to fix it

    def resolve(self, cost, time_taken):
        """maintenance staff call this when an issue is fixed"""
        self.status       = "resolved"
        self.cost         = cost
        self.time_taken   = time_taken
        self.date_resolved = str(date.today())

    def __str__(self):
        return (f"Request {self.request_id} — Apt {self.apartment_id} "
                f"— {self.priority} priority — {self.status}")


# ----------------------------------------------------------------------- #
#  APARTMENT MANAGER CLASS                                                 #
# ----------------------------------------------------------------------- #

class ApartmentManager:
    """
    handles all database operations for the apartment management component
    kept separate from the Apartment class so db logic doesnt mix with data logic
    makes unit testing easier too since we can swap the db connection in tests
    """

    # ------------------------------------------------------------------ #
    #  APARTMENT CRUD                                                     #
    # ------------------------------------------------------------------ #

    def add_apartment(self, location, apt_type, monthly_rent, num_rooms):
        """register a new apartment - validates inputs before touching the db"""
        if not location or not location.strip():
            raise ValueError("location cannot be empty")
        if not apt_type or not apt_type.strip():
            raise ValueError("apartment type cannot be empty")
        if monthly_rent <= 0:
            raise ValueError("monthly rent must be greater than 0")
        if num_rooms <= 0:
            raise ValueError("number of rooms must be at least 1")

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO apartments (location, apt_type, monthly_rent, num_rooms, status)
            VALUES (?, ?, ?, ?, 'vacant')
        """, (location.strip(), apt_type.strip(), monthly_rent, num_rooms))
        conn.commit()
        conn.close()

    def get_all_apartments(self):
        """returns every apartment as a list of Apartment objects"""
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apartments ORDER BY apartment_id")
        rows   = cursor.fetchall()
        conn.close()
        # *row unpacks the tuple so each column maps to the right __init__ param
        return [Apartment(*row) for row in rows]

    def get_apartments_by_location(self, location):
        """filter apartments by city - useful for admin and reporting components"""
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM apartments WHERE location = ? ORDER BY apartment_id",
            (location,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [Apartment(*row) for row in rows]

    def get_apartment_by_id(self, apartment_id):
        """fetch a single apartment by id - returns None if not found"""
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM apartments WHERE apartment_id = ?", (apartment_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return Apartment(*row)
        return None

    def update_apartment(self, apartment_id, location, apt_type,
                         monthly_rent, num_rooms):
        """update apartment details - admin only in the gui"""
        if monthly_rent <= 0:
            raise ValueError("monthly rent must be greater than 0")
        if num_rooms <= 0:
            raise ValueError("number of rooms must be at least 1")

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE apartments
            SET location = ?, apt_type = ?, monthly_rent = ?, num_rooms = ?
            WHERE apartment_id = ?
        """, (location, apt_type, monthly_rent, num_rooms, apartment_id))
        conn.commit()
        conn.close()

    def delete_apartment(self, apartment_id):
        """
        delete an apartment - blocked if there are open maintenance requests
        didnt want someone deleting a property that still has unresolved issues
        """
        conn   = get_connection()
        cursor = conn.cursor()

        # block deletion if any open requests exist for this apartment
        cursor.execute("""
            SELECT COUNT(*) FROM maintenance_requests
            WHERE apartment_id = ? AND status = 'open'
        """, (apartment_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise ValueError("cannot delete apartment with open maintenance requests")

        cursor.execute(
            "DELETE FROM apartments WHERE apartment_id = ?", (apartment_id,)
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------ #
    #  TENANT ASSIGNMENT                                                  #
    # ------------------------------------------------------------------ #

    def assign_tenant(self, apartment_id, tenant_id):
        """
        link a tenant to an apartment and mark it occupied
        the tenant management team should call this after creating a tenant record
        tenant_id must be a valid id from the tenants table
        """
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT status FROM apartments WHERE apartment_id = ?", (apartment_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"apartment {apartment_id} not found")
        if row[0] == "occupied":
            conn.close()
            raise ValueError("apartment is already occupied")

        cursor.execute("""
            UPDATE apartments
            SET status = 'occupied', tenant_id = ?
            WHERE apartment_id = ?
        """, (tenant_id, apartment_id))
        conn.commit()
        conn.close()

    def remove_tenant(self, apartment_id):
        """
        unlink tenant from apartment and set status back to vacant
        tenant management team should call this when a tenant ends their lease
        """
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE apartments
            SET status = 'vacant', tenant_id = NULL
            WHERE apartment_id = ?
        """, (apartment_id,))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------ #
    #  MAINTENANCE REQUESTS                                               #
    # ------------------------------------------------------------------ #

    def add_maintenance_request(self, apartment_id, description, priority):
        """
        raise a new maintenance request for an apartment
        front-desk staff or tenants (via front desk) create these
        maintenance staff will then pick them up from get_all_maintenance_requests()
        """
        if not description or not description.strip():
            raise ValueError("description cannot be empty")
        if priority not in ("low", "medium", "high"):
            raise ValueError("priority must be low, medium, or high")

        # check the apartment actually exists before adding a request for it
        if not self.get_apartment_by_id(apartment_id):
            raise ValueError(f"apartment {apartment_id} not found")

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_requests
                (apartment_id, description, priority, status, date_raised)
            VALUES (?, ?, ?, 'open', ?)
        """, (apartment_id, description.strip(), priority, str(date.today())))
        conn.commit()
        conn.close()

    def get_all_maintenance_requests(self):
        """returns all maintenance requests ordered by priority then date"""
        conn   = get_connection()
        cursor = conn.cursor()
        # order high priority first so maintenance staff see urgent ones at the top
        cursor.execute("""
            SELECT * FROM maintenance_requests
            ORDER BY
                CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                date_raised ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [MaintenanceRequest(*row) for row in rows]

    def get_requests_by_apartment(self, apartment_id):
        """get all maintenance requests for a specific apartment"""
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM maintenance_requests
            WHERE apartment_id = ?
            ORDER BY date_raised DESC
        """, (apartment_id,))
        rows = cursor.fetchall()
        conn.close()
        return [MaintenanceRequest(*row) for row in rows]

    def resolve_maintenance_request(self, request_id, cost, time_taken):
        """
        mark a maintenance request as resolved
        maintenance staff call this after finishing a job and logging their time/costs
        """
        if cost < 0:
            raise ValueError("cost cannot be negative")
        if time_taken <= 0:
            raise ValueError("time taken must be greater than 0")

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE maintenance_requests
            SET status = 'resolved', cost = ?, time_taken = ?, date_resolved = ?
            WHERE request_id = ?
        """, (cost, time_taken, str(date.today()), request_id))
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------ #
    #  REPORTING HELPERS                                                  #
    # ------------------------------------------------------------------ #

    def get_occupancy_summary(self):
        """
        returns a dict with occupancy stats - used by the reporting component
        example return: {'total': 6, 'occupied': 4, 'vacant': 2, 'rate': 66.7}
        """
        apartments = self.get_all_apartments()
        total    = len(apartments)
        occupied = sum(1 for a in apartments if a.status == "occupied")
        vacant   = total - occupied
        rate     = round((occupied / total * 100), 1) if total > 0 else 0.0
        return {
            "total":    total,
            "occupied": occupied,
            "vacant":   vacant,
            "rate":     rate
        }

    def get_maintenance_cost_summary(self):
        """
        returns total maintenance costs - used by reporting/finance components
        only counts resolved requests since open ones dont have a cost yet
        """
        requests = self.get_all_maintenance_requests()
        resolved = [r for r in requests if r.status == "resolved" and r.cost]
        total_cost = sum(r.cost for r in resolved)
        return {
            "total_requests": len(requests),
            "resolved":       len(resolved),
            "open":           len(requests) - len(resolved),
            "total_cost":     round(total_cost, 2)
        }

    # ------------------------------------------------------------------ #
    #  MOCK DATA                                                          #
    # ------------------------------------------------------------------ #

    def insert_mock_data(self):
        """
        adds realistic test data for demos and development
        only runs if the apartments table is empty so no duplicate data
        """
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM apartments")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return  # already has data, dont add again

        apartments = [
            ("Bristol",    "2-bedroom flat",   1200.00, 2),
            ("Bristol",    "1-bedroom flat",    850.00, 1),
            ("Bristol",    "Studio",            700.00, 1),
            ("London",     "3-bedroom house",  2500.00, 3),
            ("London",     "2-bedroom flat",   1800.00, 2),
            ("London",     "Studio",            950.00, 1),
            ("Manchester", "2-bedroom flat",   1100.00, 2),
            ("Manchester", "1-bedroom flat",    780.00, 1),
            ("Cardiff",    "1-bedroom flat",    750.00, 1),
            ("Cardiff",    "2-bedroom flat",    950.00, 2),
        ]

        cursor.executemany("""
            INSERT INTO apartments (location, apt_type, monthly_rent, num_rooms, status)
            VALUES (?, ?, ?, ?, 'vacant')
        """, apartments)

        # mark a couple as occupied with placeholder tenant ids
        # tenant management team will replace these with real tenant ids
        cursor.execute(
            "UPDATE apartments SET status='occupied', tenant_id=1 WHERE apartment_id=1"
        )
        cursor.execute(
            "UPDATE apartments SET status='occupied', tenant_id=2 WHERE apartment_id=4"
        )
        cursor.execute(
            "UPDATE apartments SET status='occupied', tenant_id=3 WHERE apartment_id=7"
        )

        # some example maintenance requests at different stages
        maintenance = [
            (1, "boiler not working - no hot water",           "high"),
            (2, "leaking tap in bathroom",                     "low"),
            (4, "faulty electrical socket in kitchen",         "high"),
            (5, "front door lock stiff and hard to turn",      "medium"),
            (7, "mould on bathroom ceiling",                   "medium"),
            (3, "window latch broken on ground floor",         "low"),
        ]

        for apt_id, desc, priority in maintenance:
            cursor.execute("""
                INSERT INTO maintenance_requests
                    (apartment_id, description, priority, status, date_raised)
                VALUES (?, ?, ?, 'open', ?)
            """, (apt_id, desc, priority, str(date.today())))

        # one already-resolved request so the table looks realistic
        cursor.execute("""
            INSERT INTO maintenance_requests
                (apartment_id, description, priority, status,
                 date_raised, date_resolved, cost, time_taken)
            VALUES (1, 'broken light fitting in hallway', 'low', 'resolved',
                    '2025-03-01', '2025-03-03', 45.00, 1)
        """)

        conn.commit()
        conn.close()
        print("mock data inserted ok")