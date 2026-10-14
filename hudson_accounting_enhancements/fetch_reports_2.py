import psycopg2

conn = psycopg2.connect("dbname=Hudson user=openpg password=Darklord2001@")
cur = conn.cursor()
cur.execute("""
    SELECT r.id, r.name, m.module, m.name 
    FROM account_financial_report r
    LEFT JOIN ir_model_data m ON m.res_id = r.id AND m.model = 'account.financial.report'
    WHERE r.name::text ILIKE '%profit%'
""")
for row in cur.fetchall():
    print(row)
cur.close()
conn.close()
