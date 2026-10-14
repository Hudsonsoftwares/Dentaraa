from odoo import models, fields, api, _

class AccountBudgetLine(models.Model):
    _inherit = 'account.budget.line'

    # Note: om_account_budget in Odoo 20 already provides budget_id, analytic_account_id,
    # date_from, date_to, planned_amount, practical_amount, theoretical_amount, achievement, etc.


class AccountBudget(models.Model):
    _inherit = 'account.budget'

    def action_revise_budget(self):
        self.ensure_one()
        base_name = self.name
        if " - Rev " in base_name:
            base_name = base_name.rsplit(" - Rev ", 1)[0]
        
        existing_revisions = self.search([('name', 'ilike', f"{base_name} - Rev %")])
        rev_num = 1
        for rev in existing_revisions:
            try:
                num = int(rev.name.rsplit(" - Rev ", 1)[-1])
                if num >= rev_num:
                    rev_num = num + 1
            except ValueError:
                pass

        new_name = f"{base_name} - Rev {rev_num}"
        new_budget = self.copy(default={'name': new_name, 'state': 'draft'})
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Budget Revision'),
            'res_model': 'account.budget',
            'view_mode': 'form',
            'res_id': new_budget.id,
            'target': 'current',
        }
