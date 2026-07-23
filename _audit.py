import sqlite3, json
conn = sqlite3.connect("data/products.db")
c = conn.cursor()

# Premium brands and their prices
c.execute("SELECT name, brand, price, category FROM products ORDER BY price ASC")
rows = c.fetchall()

print("=== All products sorted by price ===")
for r in rows:
    print(f"  {r[0]:45s} {r[1]:30s} {r[2]:>8}  {r[3]}")

# Check what sizes exist via data.variants
print("\n=== Products with size data ===")
c.execute("SELECT name, brand, price, data FROM products WHERE data IS NOT NULL AND data != ''")
for r in c.fetchall():
    try:
        data = json.loads(r[3])
        variants = data.get("variants", [])
        if variants:
            sizes = [f"{v.get('size','?')}({v.get('price','?')})" for v in variants if isinstance(v, dict)]
            print(f"  {r[0]:45s} {r[1]:20s} {r[2]:>8}  {', '.join(sizes[:3])}")
    except:
        pass

conn.close()
