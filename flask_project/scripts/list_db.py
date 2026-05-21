import sqlite3, os
DB=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shopuniverse_auth.db')
if not os.path.exists(DB):
    print('DB not found:', DB)
    raise SystemExit(0)
conn=sqlite3.connect(DB)
cur=conn.cursor()
print('Sellers:')
for row in cur.execute('SELECT id, full_name, email FROM sellers'):
    print(row)
print('\nProducts:')
for row in cur.execute('SELECT id, seller_id, name, price FROM products'):
    print(row)
conn.close()
