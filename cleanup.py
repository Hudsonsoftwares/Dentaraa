env = self.env
model = env['ir.model'].search([('model', '=', 'dental.branch')])
if model:
    model.unlink()
    env.cr.commit()
    print('DELETED dental.branch from ir.model')
else:
    print('NOT FOUND dental.branch')

# Let's also check ir.actions.act_window
action = env['ir.actions.act_window'].search([('res_model', '=', 'dental.branch')])
if action:
    action.unlink()
    env.cr.commit()
    print('DELETED action_dental_branch')
