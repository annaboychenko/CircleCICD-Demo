import sqlite3

db_path = "pams.db"
dump_path = "pams_dump.sql"

conn = sqlite3.connect(db_path)

with open(dump_path, "w", encoding="utf-8") as f:
    for line in conn.iterdump():
        f.write(f"{line}\n")

conn.close()

print("Database dumped to pams_dump.sql")
