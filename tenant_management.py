# Tahiyah Begum Pir - 24020023


from database import get_connection
from datetime import date, datetime


# ---------------------------------------------------------
# UPDATE TENANT
# ---------------------------------------------------------
def edit_tenant(tenant_id, name=None, email=None, phone=None):
    conn = get_connection()
    cursor = conn.cursor()

    if name:
        cursor.execute("UPDATE tenants SET full_name=? WHERE tenant_id=?", (name, tenant_id))
    if email:
        cursor.execute("UPDATE tenants SET email=? WHERE tenant_id=?", (email, tenant_id))
    if phone:
        cursor.execute("UPDATE tenants SET phone=? WHERE tenant_id=?", (phone, tenant_id))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# DELETE TENANT (FULL REMOVE)
# ---------------------------------------------------------
def delete_tenant(tenant_id):
    conn = get_connection()
    cursor = conn.cursor()

    # remove tenant from apartment first (important for integrity)
    cursor.execute("""
        UPDATE apartments 
        SET tenant_id=NULL, status='vacant' 
        WHERE tenant_id=?
    """, (tenant_id,))

    cursor.execute("DELETE FROM tenants WHERE tenant_id=?", (tenant_id,))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# EARLY TERMINATION (5% penalty)
# ---------------------------------------------------------
def calculate_early_termination_fee(tenant_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT monthly_rent FROM tenants WHERE tenant_id=?", (tenant_id,))
    row = cursor.fetchone()

    conn.close()

    if not row or not row[0]:
        return 0

    rent = row[0]
    return rent * 0.05


# ---------------------------------------------------------
# CHECK LATE PAYMENT (uses payments table)
# ---------------------------------------------------------
def check_late_payment_tenant(tenant_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status FROM payments
        WHERE tenant_id=?
    """, (tenant_id,))

    rows = cursor.fetchall()
    conn.close()

    for r in rows:
        if "late" in r[0] or r[0] == "overdue":
            return True

    return False


# ---------------------------------------------------------
# GET TENANT LEASE DETAILS
# ---------------------------------------------------------
def get_lease_details(tenant_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT lease_start, lease_end, monthly_rent, apartment_id
        FROM tenants
        WHERE tenant_id=?
    """, (tenant_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "Start of lease ": row[0],
        "End of lease ": row[1],
        "Monthly Rent": row[2],
        "Apartment ID": row[3]
    }