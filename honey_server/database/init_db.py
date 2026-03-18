import sqlite3, pathlib, os

DB_PATH = pathlib.Path(__file__).parent.parent / "database" / "mock.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users table (SQLi target for login bypass)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)

    # Products table (SQLi target for search - UNION attack)
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER,
            stock INTEGER
        )
    """)

    # Internal notes (juicy data for LFI/RCE attacker to dump)
    c.execute("""
        CREATE TABLE IF NOT EXISTS internal_notes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            created_at TEXT
        )
    """)

    # Seed data
    c.executemany("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", [
        (1, "admin_internal", "admin@honey.local",    "FLAG{SQLI_MASTER_LOGGED_IN}",              "admin"),
        (2, "hong_gildong",   "hong@honey.local",     "5f4dcc3b5aa765d61d8327deb882cf99",         "user"),
        (3, "kim_chulsu",     "chulsu@honey.local",   "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a", "user"),
        (4, "manager",        "manager@honey.local",  "03ac674216f3e15c761ee1a5e255f067953623c8",  "manager"),
    ])

    c.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)", [
        (1,  "지리산 야생화꿀",  "청정 지역 야생화에서 채밀한 100% 천연 꿀", 45000, 50),
        (2,  "프리미엄 밤꿀",    "면역력에 좋은 깊고 쌉쌀한 밤꿀",          65000, 30),
        (3,  "제주 유채꿀",     "제주도 유채꽃의 은은한 향기",             35000, 80),
    ])

    c.executemany("INSERT OR IGNORE INTO internal_notes VALUES (?,?,?,?)", [
        (1, "DB Credentials",    "prod_db_user=root\nprod_db_pass=Honey#Prod2024!\nhost=10.0.2.100:3306", "2024-01-10"),
        (2, "AWS Keys",          "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7HONEYXX\nAWS_SECRET=wJalrXUtnFEMI/K7MDENG/bPxRfiCY", "2024-02-01"),
        (3, "Admin Credentials", "admin / Honey@Admin123!", "2024-03-01"),
    ])

    conn.commit()
    conn.close()
    print(f"[DB] Initialized mock database at {DB_PATH}")

if __name__ == "__main__":
    init_db()
