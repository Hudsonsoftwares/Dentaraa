import sys
import os
sys.path.append(r"C:\Program Files\Odoo 19.0.20260518\server")
import odoo
odoo.tools.config.parse_config([
    '-c', r"C:\Program Files\Odoo 19.0.20260518\server\odoo.conf",
    '-d', 'odoo',
    '--no-http'
])
registry = odoo.modules.registry.Registry('odoo')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    reports = env['account.financial.report'].search([])
    for r in reports:
        print(f"ID: {r.id}, NAME: {r.name}, PARENT: {r.parent_id.name if r.parent_id else 'None'}")
