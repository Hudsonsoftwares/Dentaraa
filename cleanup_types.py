import psycopg2

conn = psycopg2.connect(dbname='DenBell', user='odoo', password='odoopwd', host='localhost', port=5432)
cur = conn.cursor()

# Ensure types exist
types = [
    ('Emergency Consultation', 30.0, 'Immediate relief for acute toothache, severe pain, broken teeth, or sudden oral trauma.', 50.0, 'fa-bolt', 1),
    ('Adult Full Examination', 45.0, 'Comprehensive dental check-up, intraoral scan, gum health assessment & custom treatment plan.', 75.0, 'fa-user-md', 2),
    ('Child Examination', 30.0, 'Gentle pediatric dental assessment, cavity check, fluoride review, and child-friendly hygiene tips.', 40.0, 'fa-smile-o', 3),
    ('Teeth Cleaning & Polish', 45.0, 'Ultrasonic scaling, tartar and plaque removal, stain clearance, and smooth enamel polish.', 100.0, 'fa-star', 4),
    ('Cosmetic & Whitening Consultation', 45.0, 'Aesthetic smile design, shade evaluation, veneers discussion, and laser teeth whitening plan.', 120.0, 'fa-magic', 5),
    ('Root Canal Evaluation', 60.0, 'In-depth assessment of tooth nerve vitality, pulp inflammation diagnosis, and endodontic care.', 150.0, 'fa-heartbeat', 6),
]

for name, dur, desc, pr, ic, col in types:
    cur.execute("SELECT id FROM dental_appointment_type WHERE name = %s;", (name,))
    row = cur.fetchone()
    if row:
        cur.execute("""
            UPDATE dental_appointment_type
            SET duration = %s, description = %s, price = %s, icon = %s, color = %s, active = true, write_date = NOW()
            WHERE id = %s;
        """, (dur, desc, pr, ic, col, row[0]))
    else:
        cur.execute("""
            INSERT INTO dental_appointment_type (name, duration, description, price, icon, color, active, create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, %s, true, 2, 2, NOW(), NOW());
        """, (name, dur, desc, pr, ic, col))

# Update 'Regular' to inactive or keep it
cur.execute("UPDATE dental_appointment_type SET active = false WHERE name = 'Regular';")

# Also ensure Dr. Devipriya is set to dentist role
cur.execute("""
    UPDATE hr_employee
    SET dental_role = 'dentist', specialization = 'Chief Dental Surgeon & Orthodontist'
    WHERE id = 1;
""")

# Also ensure Dr. Bob specialization is set
cur.execute("""
    UPDATE hr_employee
    SET specialization = 'Cosmetic Dentist & Implantologist'
    WHERE id = 4;
""")

conn.commit()

cur.execute('SELECT id, name, duration, price, icon FROM dental_appointment_type WHERE active = true ORDER BY id;')
rows = cur.fetchall()
for r in rows:
    print('Configured Type:', r)

cur.execute("SELECT id, name, is_dentist, dental_role, specialization FROM hr_employee WHERE is_dentist = true OR id IN (1, 4);")
docs = cur.fetchall()
for d in docs:
    print('Dentist:', d)

conn.close()
