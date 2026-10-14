import psycopg2

def get_databases():
    conn = psycopg2.connect("dbname=postgres user=openpg password=Darklord2001@")
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    dbs = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return dbs

for db in get_databases():
    try:
        conn = psycopg2.connect(f"dbname={db} user=openpg password=Darklord2001@")
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM account_financial_report WHERE name::text ILIKE '%profit%';")
        reports = cur.fetchall()
        if reports:
            print(f"--- DB: {db} ---")
            for r in reports:
                print(r)
        cur.close()
        conn.close()
    except Exception as e:
        pass
