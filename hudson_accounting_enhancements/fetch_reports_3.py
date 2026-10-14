import psycopg2

conn = psycopg2.connect("dbname=Hudson user=openpg password=Darklord2001@")
cur = conn.cursor()
cur.execute("""
    SELECT id, name, parent_id, sequence 
    FROM account_financial_report
    WHERE id IN (53, 54, 86, 87)
""")
for row in cur.fetchall():
    print(row)
cur.close()
conn.close()
