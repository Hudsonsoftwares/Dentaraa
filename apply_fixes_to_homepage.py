# -*- coding: utf-8 -*-
"""
Apply appointment workflow fixes directly to homepage views 3204 and 3253,
which render the root URL http://localhost:8069/ (with TREATMENTS, ABOUT US navbar).
"""
import psycopg2
import xmlrpc.client
import json

conn = psycopg2.connect(dbname='DenBell', user='odoo', password='odoopwd', host='localhost', port=5432)
cur = conn.cursor()

# 1. Fetch updated snippet from view 3258
cur.execute("SELECT arch_db FROM ir_ui_view WHERE id = 3258;")
v3258_text = cur.fetchone()[0]['en_US']
pos_start = v3258_text.find('<!-- FONT AWESOME ICONS CDN -->')
pos_end = v3258_text.rfind('</script>') + len('</script>')
updated_snippet = v3258_text[pos_start:pos_end]

print("Updated snippet extracted. Length:", len(updated_snippet))
assert 'font-awesome' in updated_snippet
assert 'scrollIntoView' in updated_snippet
assert 'scrollTo({ top: 120' not in updated_snippet

# 2. Update views 3204 (website.homepage) and 3253
updated_views = {}
for view_id in [3204, 3253]:
    cur.execute("SELECT arch_db FROM ir_ui_view WHERE id = %s;", (view_id,))
    v_arch = cur.fetchone()[0]
    content = v_arch['en_US']

    # Locate appointment flow in homepage content
    pos1 = content.find('<!-- FONT AWESOME ICONS CDN -->')
    if pos1 == -1:
        pos1 = content.find('<!-- INLINE STYLES FOR FUTURISTIC DENTAL WORKFLOW -->')
    assert pos1 != -1, f"Could not find appointment section start in view {view_id}"

    pos2 = content.find('</script>', pos1) + len('</script>')
    assert pos2 > pos1, f"Could not find appointment section end in view {view_id}"

    new_content = content[:pos1] + updated_snippet + content[pos2:]
    updated_views[view_id] = new_content

    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = %s, write_date = NOW()
        WHERE id = %s;
    """, (json.dumps({"en_US": new_content}), view_id))
    print(f"Updated view {view_id} in PostgreSQL successfully! (Original len: {len(content)}, New len: {len(new_content)})")

conn.commit()
conn.close()

# 3. Invalidate Odoo ORM view cache via XML-RPC
common = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/common')
uid = common.authenticate('DenBell', 'sijikumardevipriya@gmail.com', 'admin', {})
models = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/object')

for view_id, new_content in updated_views.items():
    models.execute_kw('DenBell', uid, 'admin', 'ir.ui.view', 'write', [[view_id], {
        'arch_db': {'en_US': new_content}
    }])
    print(f"Synced view {view_id} in Odoo ORM via XML-RPC successfully!")

print("\nALL HOMEPAGE VIEWS SUCCESSFULLY UPDATED!")
