# Anna Boychenko - 24030024
# shared database setup for the whole PAMS project
# every component imports get_connection() from here to talk to the same sqlite db
# using sqlite3 because its built into python and doesnt need installing separately
# the db file is called pams.db and sits in the project root folder

import sqlite3
import os

# path to the shared database file - all components use this same file
DB_PATH=os.path.join(os.path.dirname(os.path.abspath(__file__)), "pams.db")


def get_connection():
    """returns a connection to the shared pams sqlite database"""
    conn=sqlite3.connect(DB_PATH)
    # foreign keys are off by default in sqlite so we turn them on every connection
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialise_database():
    """
    creates all the tables if they dont exist yet
    this is called once at startup so the schema is always ready
    other group members should add their own tables here too so everything
    stays in one place and we dont end up with multiple db files
    """
    conn=get_connection()
    cursor=conn.cursor()

    # ------------------------------------------------------------------ #
    #  APARTMENTS TABLE - owned by anna (apartment management component)  #
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    #  MAINTENANCE REQUESTS - owned by anna (apartment management)        #
    #  maintenance staff component will also read/update this table       #
    # ------------------------------------------------------------------ #
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
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        )
    """)

    # ------------------------------------------------------------------ #
    #  USERS TABLE - placeholder for the user/account management team     #
    #  front-desk staff, finance managers, maintenance staff, admins      #
    #  this team will expand this table with password hashing etc         #
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    #  TENANTS TABLE - Grace                                             #
    #  they will add lease, payment history and complaint fields          #
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    #  PAYMENTS TABLE - Grace                                            #
    #  they will expand this with invoice generation and late fees        #
    # ------------------------------------------------------------------ #
   
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
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
        )
    """)



    conn.commit()
    conn.close()


# run schema setup when this module is imported for the first time
initialise_database()