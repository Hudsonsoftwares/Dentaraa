import psycopg2

conn = psycopg2.connect("dbname=Hudson user=openpg password=Darklord2001@")
cur = conn.cursor()
cur.execute("""
    DELETE FROM account_financial_report 
    WHERE id IN (
        SELECT r.id 
        FROM account_financial_report r
        LEFT JOIN ir_model_data m ON m.res_id = r.id AND m.model = 'account.financial.report'
        WHERE m.id IS NULL
    )
""")
conn.commit()
cur.close()
conn.close()
