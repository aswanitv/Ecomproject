import sqlite3, os
DB=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shopuniverse_auth.db')
if not os.path.exists(DB):
    print('DB not found:', DB)
    raise SystemExit(1)
conn=sqlite3.connect(DB)
cur=conn.cursor()
# Simple heuristics mapping keywords to categories
mappings=[('party', 'Party'), ('shimmer', 'Party'), ('sequin', 'Party'), ('cotton','Casual'), ('denim','Casual'), ('floral','Casual'), ('casual','Casual'), ('anarkali','Ethnic'), ('lehenga','Ethnic'), ('saree','Ethnic'), ('kurti','Ethnic')]
cur.execute('SELECT id, name FROM products')
for pid, name in cur.fetchall():
    lname = (name or '').lower()
    assigned = None
    for k, cat in mappings:
        if k in lname:
            assigned = cat
            break
    if assigned:
        cur.execute('UPDATE products SET category=? WHERE id=?', (assigned, pid))
        print('Set', pid, name, '->', assigned)
conn.commit()
conn.close()
print('Done')
