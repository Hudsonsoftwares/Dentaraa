import psycopg2
import xmlrpc.client
import json

# 1. Connect to PostgreSQL
conn = psycopg2.connect(dbname='DenBell', user='odoo', password='odoopwd', host='localhost', port=5432)
cur = conn.cursor()

# 2. Get the new workflow markup from apply_redesign_workflow.py
import apply_redesign_workflow
workflow_full = apply_redesign_workflow.template_content

start_marker = "<!-- INLINE STYLES FOR FUTURISTIC DENTAL WORKFLOW -->"
end_marker = "</script>"
idx_start = workflow_full.find(start_marker)
idx_end = workflow_full.find(end_marker, idx_start) + len(end_marker)

assert idx_start != -1 and idx_end != -1, "Could not extract workflow block from template_content"
workflow_block = workflow_full[idx_start:idx_end]
print(f"Extracted workflow block ({len(workflow_block)} characters)")

# In workflow_block, ensure <section class="dental-flow-wrapper" id="appointment">
if '<section class="dental-flow-wrapper" id="appointment">' not in workflow_block:
    workflow_block = workflow_block.replace('<section class="dental-flow-wrapper">', '<section class="dental-flow-wrapper" id="appointment">')

# 3. Find all views containing dw-appt-form or the old appointment section
cur.execute("SELECT id, key, name FROM ir_ui_view WHERE arch_db::text LIKE '%dw-appt-form%' OR id IN (3204, 3253)")
target_views = cur.fetchall()
print(f"Found {len(target_views)} target views to update:", target_views)

common = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/common')
uid = common.authenticate('DenBell', 'sijikumardevipriya@gmail.com', 'admin', {})
models = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/object')

for v_id, v_key, v_name in target_views:
    cur.execute("SELECT arch_db FROM ir_ui_view WHERE id = %s", (v_id,))
    arch_raw = cur.fetchone()[0]
    arch_dict = arch_raw if isinstance(arch_raw, dict) else json.loads(arch_raw)
    html_content = arch_dict.get('en_US', '')

    old_start = html_content.find('<section id="appointment"')
    if old_start != -1:
        old_end = html_content.find('</section>', old_start) + len('</section>')
        new_html = html_content[:old_start] + workflow_block + html_content[old_end:]
        print(f"Replacing <section id='appointment'> in view {v_id} ({v_key})...")
    else:
        # Check if dw-appt-form is present
        form_start = html_content.find('dw-appt-form')
        if form_start != -1:
            print(f"dw-appt-form present in view {v_id} without section id='appointment', replacing panel...")
            panel_start = html_content.rfind('<div class="dw-appt-form-panel', 0, form_start)
            panel_end = html_content.find('</div>', form_start) + len('</div>')
            new_html = html_content[:panel_start] + workflow_block + html_content[panel_end:]
        else:
            print(f"View {v_id} already has updated content.")
            continue

    assert 'dw-appt-form' not in new_html, f"Failed to eradicate dw-appt-form from view {v_id}"

    # Update in DB
    cur.execute("UPDATE ir_ui_view SET arch_db = %s, write_date = NOW() WHERE id = %s", (json.dumps({"en_US": new_html}), v_id))
    conn.commit()

    # Flush ORM cache
    models.execute_kw('DenBell', uid, 'admin', 'ir.ui.view', 'write', [[v_id], {
        'arch_db': {'en_US': new_html}
    }])
    print(f"View {v_id} ({v_key}) successfully updated in PostgreSQL and XML-RPC cache flushed!")

conn.close()
print("\n>>> ALL HOMEPAGE VIEWS SUCCESSFULLY UPDATED WITH 6-STEP WORKFLOW! <<<")
