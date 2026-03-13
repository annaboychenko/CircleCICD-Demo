import sqlite3

def get_connection():
    conn = sqlite3.connect("pams.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    conn = get_connection()
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
    cursor.close()
    conn.close()
    print("Tables created successfully")

if __name__ == "__main__":
    create_tables()