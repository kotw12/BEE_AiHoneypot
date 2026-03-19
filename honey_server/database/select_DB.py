import sqlite3

conn = sqlite3.connect('honeypot.db')
cursor = conn.cursor()

tables = ['users', 'products', 'orders', 'order_details']

for table in tables:
    print(f"\n--- {table} ---")
    cursor.execute(f"SELECT * FROM {table};")
    rows = cursor.fetchall()
    
    if not rows:
        print("데이터가 없습니다.")
    else:
        for row in rows:
            print(row)

conn.close()