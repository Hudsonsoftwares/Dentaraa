from odoo import api, fields, models

class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    # Old reconcile method removed
    
    def action_hudson_upload_bills(self):
        """ Open a wizard or form to attach/upload bills """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }

    @api.model
    def action_hudson_dummy_upload(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Upload', 'message': 'Upload feature triggered!', 'sticky': False}
        }

    hudson_action_dummy = fields.Boolean(compute='_compute_hudson_action_dummy')
    def _compute_hudson_action_dummy(self):
        for rec in self:
            rec.hudson_action_dummy = False

    # --- New UI Backend Fields & Methods ---
    
    hudson_matched_account_name = fields.Char(
        string='Matched Account', 
        compute='_compute_hudson_matched_account_name',
        store=False
    )
    
    @api.depends('is_reconciled', 'move_id.line_ids.reconciled')
    def _compute_hudson_matched_account_name(self):
        for line in self:
            if not line.is_reconciled:
                line.hudson_matched_account_name = False
                continue
            # Try to find the counter-part account in the move lines
            liquidity_lines = line.move_id.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_cash', 'liability_credit_card'))
            counterpart_lines = line.move_id.line_ids - liquidity_lines
            if counterpart_lines:
                # E.g. "100400 Debtors"
                acc = counterpart_lines[0].account_id
                line.hudson_matched_account_name = f"{acc.code} {acc.name}"
            else:
                line.hudson_matched_account_name = 'Reconciled'

    hudson_account_id = fields.Many2one(
        'account.account',
        string="Account",
        help="Temporary account field for new statement lines."
    )
    
    def write(self, vals):
        res = super(AccountBankStatementLine, self).write(vals)
        if 'hudson_account_id' in vals and vals.get('hudson_account_id'):
            for line in self:
                bank_account = line.journal_id.default_account_id
                suspense_lines = line.line_ids.filtered(lambda l: l.account_id != bank_account)
                if suspense_lines:
                    if line.move_id.state == 'posted':
                        line.move_id.button_draft()
                    suspense_lines[0].write({'account_id': vals['hudson_account_id']})
                    line.move_id.action_post()
                    # Just setting the account acts as a manual match, so we consider it reconciled
                    line.hudson_matched_account_name = self.env['account.account'].browse(vals['hudson_account_id']).name
        return res

    hudson_has_matches = fields.Boolean(
        string='Has Matches',
        compute='_compute_hudson_has_matches',
        store=False
    )

    @api.depends('is_reconciled', 'amount')
    def _compute_hudson_has_matches(self):
        for line in self:
            if line.is_reconciled:
                line.hudson_has_matches = False
                continue
                
            domain = [
                ('account_id.reconcile', '=', True),
                ('reconciled', '=', False),
                ('move_id.state', '=', 'posted'),
                ('company_id', '=', line.company_id.id),
                ('amount_residual', '=', line.amount),
                ('journal_id.type', 'not in', ('bank', 'cash'))
            ]
            has_match = self.env['account.move.line'].search_count(domain, limit=1)
            line.hudson_has_matches = bool(has_match)

    def action_hudson_reconcile_items(self, item_ids):
        """ Reconciles the statement line with the selected move line ids """
        self.ensure_one()
        if not item_ids:
            return True
            
        matching_lines = self.env['account.move.line'].browse(item_ids)
        if not matching_lines:
            return True
            
        # Identify the suspense/outstanding line
        bank_account = self.journal_id.default_account_id
        suspense_lines = self.line_ids.filtered(lambda l: l.account_id != bank_account)
        
        if suspense_lines:
            suspense_line = suspense_lines[0]
            first_match = matching_lines[0]
            
            # Temporarily unpost to change the account safely
            if self.move_id.state == 'posted':
                self.move_id.button_draft()
                
            suspense_line.write({
                'account_id': first_match.account_id.id,
                'partner_id': first_match.partner_id.id if first_match.partner_id else False,
            })
            
            self.move_id.action_post()
            
            # Execute native Odoo reconciliation!
            (suspense_line + matching_lines).reconcile()
            
            # Update UI field
            self.hudson_matched_account_name = first_match.account_id.name
            
        return True

    def action_hudson_internal_transfer(self):
        """ Reconciles the statement line as an internal transfer """
        self.ensure_one()
        self.is_reconciled = True
        self.hudson_matched_account_name = "Internal Transfer"
        return True

    def action_hudson_reset(self):
        """ Resets the statement line matching natively """
        self.ensure_one()
        
        # Perform native Odoo un-reconciliation to break the ledger match
        if self.is_reconciled:
            self.action_undo_reconciliation()
            
        # Restore suspense account
        bank_account = self.journal_id.default_account_id
        suspense_lines = self.line_ids.filtered(lambda l: l.account_id != bank_account)
        suspense_account = self.journal_id.suspense_account_id
        if suspense_lines and suspense_account and suspense_lines[0].account_id != suspense_account:
            if self.move_id.state == 'posted':
                self.move_id.button_draft()
            suspense_lines[0].write({'account_id': suspense_account.id, 'partner_id': False})
            self.move_id.action_post()
            
        self.is_reconciled = False
        self.hudson_matched_account_name = False
        return True

    def action_set_partner(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'hudson_set_partner',
            'context': {
                'default_statement_line_id': self.id,
            }
        }
        
    def action_set_account(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'hudson_set_account',
            'context': {
                'default_statement_line_id': self.id,
            }
        }
        
    def action_needs_attention(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Attention', 'message': 'Needs attention!', 'sticky': False}
        }
        
    def action_hudson_reset(self):
        self.ensure_one()
        self.action_undo_reconciliation()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Reset', 'message': 'Transaction un-reconciled.', 'sticky': False}
        }

    def action_expand_line(self):
        self.ensure_one()
        # Open standard form view for the statement line
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement.line',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
