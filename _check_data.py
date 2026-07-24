import json
import sqlite3

conn = sqlite3.connect('data/products.db')

names = [
    "BURBERRY HER", "GOOD GIRL", "BLACK OPIUM",
    "DIOR SAUVAGE", "BLEU DE CHANEL", "CREED AVENTUS",
    "TOBACCO VANILLE", "STRONGER WITH YOU",
    "LATTAFA KHAMRAH", "YARA", "VANILLA 28",
    "BOMBSHELL", "CK ONE", "AQUA DI GIO",
]

placeholders = ",".join("?" for _ in names)
rows = conn.execute(f"SELECT name, brand, data FROM products WHERE name IN ({placeholders})", names).fetchall()

for r in rows:
    n, b, d = r[0], r[1], (r[2] or '')
    if d:
        try:
            parsed = json.loads(d)
            fd = parsed.get('fragrance_details', {})
            desc = r[0]
        except:
            fd = {}
    else:
        fd = {}
    print(f"{n:30s} | {b:20s} | data: {bool(d)} | fd keys: {list(fd.keys()) if fd else 'NONE'}")

conn.close()
