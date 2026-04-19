from database import get_connection


class ReportManager:
    """Handles occupancy, financial, and maintenance reporting."""

    def get_occupancy_by_city(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                location,
                COUNT(*) AS total_apartments,
                SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) AS occupied,
                SUM(CASE WHEN status = 'vacant' THEN 1 ELSE 0 END) AS vacant
            FROM apartments
            GROUP BY location
            ORDER BY location
        """)

        rows = cursor.fetchall()
        conn.close()

        results = []
        for location, total, occupied, vacant in rows:
            occupied = occupied or 0
            vacant = vacant or 0
            rate = round((occupied / total) * 100, 2) if total else 0

            results.append({
                "location": location,
                "total_apartments": total,
                "occupied": occupied,
                "vacant": vacant,
                "occupancy_rate": rate
            })

        return results

    def get_occupancy_by_apartment(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT apartment_id, location, apt_type, monthly_rent, num_rooms, status, tenant_id
            FROM apartments
            ORDER BY apartment_id
        """)

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                "apartment_id": row[0],
                "location": row[1],
                "apt_type": row[2],
                "monthly_rent": row[3],
                "num_rooms": row[4],
                "status": row[5],
                "tenant_id": row[6]
            })

        return results

    def get_occupancy_for_city(self, city_name):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                location,
                COUNT(*) AS total_apartments,
                SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) AS occupied,
                SUM(CASE WHEN status = 'vacant' THEN 1 ELSE 0 END) AS vacant
            FROM apartments
            WHERE location = ?
            GROUP BY location
        """, (city_name,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                "location": city_name,
                "total_apartments": 0,
                "occupied": 0,
                "vacant": 0,
                "occupancy_rate": 0
            }

        location, total, occupied, vacant = row
        occupied = occupied or 0
        vacant = vacant or 0
        rate = round((occupied / total) * 100, 2) if total else 0

        return {
            "location": location,
            "total_apartments": total,
            "occupied": occupied,
            "vacant": vacant,
            "occupancy_rate": rate
        }

    def get_financial_summary(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_invoices,
                SUM(amount) AS total_billed,
                SUM(CASE WHEN status IN ('paid', 'paid (late)') THEN amount ELSE 0 END) AS collected_rent,
                SUM(CASE WHEN status = 'unpaid' THEN amount ELSE 0 END) AS pending_rent,
                SUM(CASE WHEN status = 'overdue' THEN amount ELSE 0 END) AS overdue_rent
            FROM invoices
        """)

        row = cursor.fetchone()
        conn.close()

        total_invoices = row[0] or 0
        total_billed = row[1] or 0
        collected_rent = row[2] or 0
        pending_rent = row[3] or 0
        overdue_rent = row[4] or 0

        collection_rate = round((collected_rent / total_billed) * 100, 2) if total_billed else 0

        return {
            "total_invoices": total_invoices,
            "total_billed": total_billed,
            "collected_rent": collected_rent,
            "pending_rent": pending_rent,
            "overdue_rent": overdue_rent,
            "collection_rate": collection_rate
        }

    def get_maintenance_summary(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_requests,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_requests,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_requests,
                SUM(CASE WHEN status = 'resolved' THEN cost ELSE 0 END) AS total_maintenance_cost
            FROM maintenance_requests
        """)

        row = cursor.fetchone()
        conn.close()

        return {
            "total_requests": row[0] or 0,
            "resolved_requests": row[1] or 0,
            "open_requests": row[2] or 0,
            "total_maintenance_cost": row[3] or 0
        }

    def get_maintenance_costs_by_city(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                a.location,
                COUNT(m.request_id) AS total_requests,
                SUM(CASE WHEN m.status = 'resolved' THEN m.cost ELSE 0 END) AS total_cost
            FROM maintenance_requests m
            JOIN apartments a ON m.apartment_id = a.apartment_id
            GROUP BY a.location
            ORDER BY a.location
        """)

        rows = cursor.fetchall()
        conn.close()

        results = []
        for location, total_requests, total_cost in rows:
            results.append({
                "location": location,
                "total_requests": total_requests,
                "total_cost": total_cost or 0
            })

        return results

    def get_maintenance_costs_for_city(self, city_name):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                a.location,
                COUNT(m.request_id) AS total_requests,
                SUM(CASE WHEN m.status = 'resolved' THEN m.cost ELSE 0 END) AS total_cost
            FROM maintenance_requests m
            JOIN apartments a ON m.apartment_id = a.apartment_id
            WHERE a.location = ?
            GROUP BY a.location
        """, (city_name,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                "location": city_name,
                "total_requests": 0,
                "total_cost": 0
            }

        return {
            "location": row[0],
            "total_requests": row[1],
            "total_cost": row[2] or 0
        }

    def get_maintenance_costs_for_apartment(self, apartment_id):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                apartment_id,
                COUNT(request_id) AS total_requests,
                SUM(CASE WHEN status = 'resolved' THEN cost ELSE 0 END) AS total_cost
            FROM maintenance_requests
            WHERE apartment_id = ?
            GROUP BY apartment_id
        """, (apartment_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                "apartment_id": apartment_id,
                "total_requests": 0,
                "total_cost": 0
            }

        return {
            "apartment_id": row[0],
            "total_requests": row[1],
            "total_cost": row[2] or 0
        }

    def generate_full_report(self):
        return {
            "occupancy_by_city": self.get_occupancy_by_city(),
            "occupancy_by_apartment": self.get_occupancy_by_apartment(),
            "financial_summary": self.get_financial_summary(),
            "maintenance_summary": self.get_maintenance_summary(),
            "maintenance_costs_by_city": self.get_maintenance_costs_by_city()
        } 