from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HudsonAutoReconcileWizard(models.TransientModel):
    _name = 'hudson.auto.reconcile.wizard'
    _description = 'Auto Reconcile Wizard'

    reconcile_mode = fields.Selection([
        ('perfect', 'Perfect Match'),
        ('clear', 'Clear Account')
    ], string='Reconcile', default='perfect', required=True)

    account_ids = fields.Many2many('account.account', string='Accounts', 
                                   domain="[('reconcile', '=', True)]")
    partner_ids = fields.Many2many('res.partner', string='Partners')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')

    @api.model
    def default_get(self, fields_list):
        res = super(HudsonAutoReconcileWizard, self).default_get(fields_list)
        if self._context.get('active_model') == 'account.move.line' and self._context.get('active_ids'):
            lines = self.env['account.move.line'].browse(self._context.get('active_ids'))
            accounts = lines.mapped('account_id')
            partners = lines.mapped('partner_id')
            if 'account_ids' in fields_list and accounts:
                res['account_ids'] = [(6, 0, accounts.ids)]
            if 'partner_ids' in fields_list and partners:
                res['partner_ids'] = [(6, 0, partners.ids)]
        return res

    def action_reconcile(self):
        # Build domain to fetch unreconciled journal items
        domain = [
            ('parent_state', '=', 'posted'),
            ('reconciled', '=', False),
            ('account_id.reconcile', '=', True),
            ('amount_residual', '!=', 0),
        ]
        
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))

        lines = self.env['account.move.line'].search(domain, order='date ASC')
        if not lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Auto-reconciliation Complete'),
                    'message': _('Nothing to reconcile. No unreconciled journal items found.'),
                    'type': 'warning',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        reconciled_count = 0

        # Group lines by Account and Partner
        grouped_lines = {}
        for line in lines:
            key = (line.account_id.id, line.partner_id.id)
            if key not in grouped_lines:
                grouped_lines[key] = self.env['account.move.line']
            grouped_lines[key] |= line

        for (account_id, partner_id), group in grouped_lines.items():
            if self.reconcile_mode == 'clear':
                # Reconcile all lines in the group if sum of residual is 0
                # Odoo's reconcile() standardly checks if sum is 0, but we can double check
                if group.currency_id.is_zero(sum(group.mapped('amount_residual_currency'))):
                    try:
                        group.reconcile()
                        reconciled_count += len(group)
                    except Exception:
                        pass
            elif self.reconcile_mode == 'perfect':
                # Find exact matching debit and credit pairs
                unreconciled_group = group
                while len(unreconciled_group) >= 2:
                    found_match = False
                    for line1 in unreconciled_group:
                        for line2 in unreconciled_group:
                            if line1.id != line2.id and line1.currency_id == line2.currency_id:
                                if line1.amount_residual_currency == -line2.amount_residual_currency:
                                    try:
                                        (line1 | line2).reconcile()
                                        reconciled_count += 2
                                        found_match = True
                                        # Remove from unreconciled set
                                        unreconciled_group -= (line1 | line2)
                                        break
                                    except Exception:
                                        pass
                        if found_match:
                            break
                    if not found_match:
                        break # No more perfect matches in this group

        if reconciled_count == 0:
            message = _('Nothing to reconcile.')
            msg_type = 'warning'
        else:
            message = _('Successfully reconciled %s journal items.', reconciled_count)
            msg_type = 'success'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-reconciliation Complete'),
                'message': message,
                'type': msg_type,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
