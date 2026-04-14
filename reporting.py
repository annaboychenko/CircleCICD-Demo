from database import get_connection


class ReportManager:
    """Reporting functions for PAMS."""

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
        for row in rows:
            location, total, occupied, vacant = row
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
            SELECT apartment_id, location, apt_type, status, tenant_id
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
                "status": row[3],
                "tenant_id": row[4]
            })

        return results

    def get_financial_summary(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_invoices,
                SUM(CASE WHEN status IN ('paid', 'paid (late)') THEN amount ELSE 0 END) AS collected_rent,
                SUM(CASE WHEN status = 'unpaid' THEN amount ELSE 0 END) AS pending_rent,
                SUM(CASE WHEN status = 'overdue' THEN amount ELSE 0 END) AS overdue_rent
            FROM invoices
        """)

        row = cursor.fetchone()
        conn.close()

        return {
            "total_invoices": row[0] or 0,
            "collected_rent": row[1] or 0,
            "pending_rent": row[2] or 0,
            "overdue_rent": row[3] or 0
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
        for row in rows:
            results.append({
                "location": row[0],
                "total_requests": row[1],
                "total_cost": row[2] or 0
            })

        return results