BEGIN TRANSACTION;
CREATE TABLE apartments (
            apartment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            location       TEXT    NOT NULL,
            apt_type       TEXT    NOT NULL,
            monthly_rent   REAL    NOT NULL,
            num_rooms      INTEGER NOT NULL,
            status         TEXT    NOT NULL DEFAULT 'vacant',
            tenant_id      INTEGER DEFAULT NULL
        );
INSERT INTO "apartments" VALUES(1,'Bristol','2-bedroom flat',1200.0,2,'occupied',1);
INSERT INTO "apartments" VALUES(2,'Bristol','1-bedroom flat',850.0,1,'vacant',NULL);
INSERT INTO "apartments" VALUES(3,'Bristol','Studio',700.0,1,'vacant',NULL);
INSERT INTO "apartments" VALUES(4,'London','3-bedroom house',2500.0,3,'occupied',2);
INSERT INTO "apartments" VALUES(5,'London','2-bedroom flat',1800.0,2,'vacant',NULL);
INSERT INTO "apartments" VALUES(6,'London','Studio',950.0,1,'vacant',NULL);
INSERT INTO "apartments" VALUES(7,'Manchester','2-bedroom flat',1100.0,2,'occupied',3);
INSERT INTO "apartments" VALUES(8,'Manchester','1-bedroom flat',780.0,1,'vacant',NULL);
INSERT INTO "apartments" VALUES(9,'Cardiff','1-bedroom flat',750.0,1,'vacant',NULL);
INSERT INTO "apartments" VALUES(10,'Cardiff','2-bedroom flat',950.0,2,'vacant',NULL);
CREATE TABLE invoices (
            invoice_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id      INTEGER NOT NULL,
            apartment_id   INTEGER NOT NULL,
            issue_date     TEXT NOT NULL,
            due_date       TEXT NOT NULL,
            amount         REAL NOT NULL,
            status         TEXT NOT NULL DEFAULT 'unpaid',
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        );
INSERT INTO "invoices" VALUES(1,3,7,'01-04-2026','10-03-2026',1100.0,'overdue');
INSERT INTO "invoices" VALUES(2,4,3,'2026-04-20','30-04-2026',700.0,'unpaid');
CREATE TABLE maintenance_notifications (
                notif_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                apartment_id   INTEGER NOT NULL,
                tenant_name    TEXT    NOT NULL,
                worker_name    TEXT    NOT NULL,
                scheduled_date TEXT    NOT NULL,
                scheduled_time TEXT    NOT NULL,
                description    TEXT    NOT NULL,
                created_at     TEXT    NOT NULL
            );
INSERT INTO "maintenance_notifications" VALUES(1,7,'Chloe Davis','System','-','-','Overdue rent Payment','20-04-2026 14:15');
CREATE TABLE maintenance_requests (
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
        );
INSERT INTO "maintenance_requests" VALUES(1,1,'boiler not working - no hot water','High','open','2026-04-20',NULL,NULL,NULL,NULL);
INSERT INTO "maintenance_requests" VALUES(2,2,'leaking tap in bathroom','Low','open','2026-04-20',NULL,NULL,NULL,NULL);
INSERT INTO "maintenance_requests" VALUES(3,4,'faulty electrical socket in kitchen','High','open','2026-04-20',NULL,NULL,NULL,NULL);
INSERT INTO "maintenance_requests" VALUES(4,5,'front door lock stiff and hard to turn','Medium','open','2026-04-20',NULL,NULL,NULL,NULL);
INSERT INTO "maintenance_requests" VALUES(5,7,'mould on bathroom ceiling','Medium','open','2026-04-20',NULL,NULL,NULL,NULL);
INSERT INTO "maintenance_requests" VALUES(6,3,'window latch broken on ground floor','Low','open','2026-04-20',NULL,NULL,NULL,NULL);
INSERT INTO "maintenance_requests" VALUES(7,1,'broken light fitting in hallway','Low','resolved','2025-03-01','2025-03-03',45.0,1,NULL);
CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
INSERT INTO "notifications" VALUES(1,'Invoice 1 for Tenant 3 is overdue (due 10-03-2026).','2026-04-20');
INSERT INTO "notifications" VALUES(2,'Invoice 1 for Tenant 3 is overdue (due 10-03-2026).','2026-04-20');
CREATE TABLE payments (
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
        );
INSERT INTO "payments" VALUES(1,3,7,1,1100.0,'10-03-2026','2026-04-20','paid (late)');
INSERT INTO "payments" VALUES(2,4,3,2,700.0,'30-04-2026',NULL,'pending');
CREATE TABLE tenants (
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
        );
INSERT INTO "tenants" VALUES(1,'Bristol','Alice Johnson','alice@example.com','07123456789','AB123456C','Engineer','Paul Jones',1,'12 months','01-01-2025','01-01-2026',1200.0,1200.0);
INSERT INTO "tenants" VALUES(2,'London','Ben Smith','ben@example.com','07234567890','CD234567D','Teacher','Alan Brown',4,'12 months','01-02-2025','01-02-2026',2500.0,2500.0);
INSERT INTO "tenants" VALUES(3,'Manchester','Chloe Davis','chloe@example.com','07345678901','EF345678E','Designer','Clive Lewis',7,'12 months','01-03-2025','01-03-2026',1100.0,1100.0);
INSERT INTO "tenants" VALUES(4,'Bristol','John Doe','john@email.com','0712345678','AB123456J','Engineer','Elliot Brown',NULL,'6 months',NULL,NULL,NULL,NULL);
CREATE TABLE users (
            user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            role       TEXT    NOT NULL DEFAULT 'front_desk',
            location   TEXT    DEFAULT NULL,
            full_name  TEXT    DEFAULT NULL,
            email      TEXT    DEFAULT NULL
        );
INSERT INTO "users" VALUES(1,'admin','admin123','admin','Bristol','Admin User','admin@pams.com');
INSERT INTO "users" VALUES(2,'manager','manager123','manager','Bristol','Manager User','manager@pams.com');
INSERT INTO "users" VALUES(3,'frontdesk','frontdesk123','front_desk','Bristol','Front Desk','frontdesk@pams.com');
INSERT INTO "users" VALUES(4,'finance','finance123','finance','Bristol','Finance Manager','finance@pams.com');
INSERT INTO "users" VALUES(5,'maintenance','maintenance123','maintenance','Bristol','Maintenance Staff','maintenance@pams.com');
CREATE TABLE worker_assignments (
                assignment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_name    TEXT    NOT NULL,
                scheduled_date TEXT    NOT NULL,
                scheduled_time TEXT    NOT NULL,
                request_id     INTEGER NOT NULL
            );
CREATE TABLE workers (
            worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            location  TEXT NOT NULL
        );
INSERT INTO "workers" VALUES(1,'Jake Smith','Bristol');
INSERT INTO "workers" VALUES(2,'Michael Brown','Bristol');
INSERT INTO "workers" VALUES(3,'Lily Evans','London');
INSERT INTO "workers" VALUES(4,'Mia Taylor','London');
INSERT INTO "workers" VALUES(5,'Charlie Davis','Manchester');
INSERT INTO "workers" VALUES(6,'Sara Wilson','Cardiff');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('users',5);
INSERT INTO "sqlite_sequence" VALUES('workers',6);
INSERT INTO "sqlite_sequence" VALUES('apartments',10);
INSERT INTO "sqlite_sequence" VALUES('maintenance_requests',7);
INSERT INTO "sqlite_sequence" VALUES('tenants',4);
INSERT INTO "sqlite_sequence" VALUES('invoices',2);
INSERT INTO "sqlite_sequence" VALUES('payments',2);
INSERT INTO "sqlite_sequence" VALUES('notifications',2);
INSERT INTO "sqlite_sequence" VALUES('maintenance_notifications',1);
COMMIT;
