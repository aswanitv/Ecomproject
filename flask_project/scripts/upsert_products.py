import sqlite3, os
from datetime import datetime
DB=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shopuniverse_auth.db')
if not os.path.exists(DB):
    print('DB not found:', DB)
    raise SystemExit(1)
conn=sqlite3.connect(DB)
cur=conn.cursor()
now=datetime.utcnow().isoformat()
products=[
    {
        'name':'Black Sequin Dress',
        'price':1999.0,
        'image_url':'/static/img/blck.jpeg',
        'description':'Shine with confidence in this glamorous black sequin dress. Designed for night parties and special events, it adds sparkle and elegance to your overall look.',
        'seller_id':7,
    },
    {
        'name':'Cotton Daily Wear',
        'price':699.0,
        'image_url':'/static/img/third.jpeg',
        'description':'Experience all-day comfort with this soft cotton daily wear dress. Perfect for regular use, office wear, and relaxed outings.',
        'seller_id':7,
    }
]
for p in products:
    cur.execute('SELECT id, name, price FROM products WHERE lower(name)=lower(?)', (p['name'],))
    row=cur.fetchone()
    if row:
        pid=row[0]
        cur.execute('UPDATE products SET seller_id=?, price=?, description=?, image_url=?, created_at=? WHERE id=?', (p['seller_id'], p['price'], p['description'], p['image_url'], now, pid))
        print('Updated product', pid, p['name'])
    else:
        cur.execute('INSERT INTO products (seller_id, name, price, description, image_url, created_at) VALUES (?,?,?,?,?,?)', (p['seller_id'], p['name'], p['price'], p['description'], p['image_url'], now))
        print('Inserted product', cur.lastrowid, p['name'])
conn.commit()
conn.close()
