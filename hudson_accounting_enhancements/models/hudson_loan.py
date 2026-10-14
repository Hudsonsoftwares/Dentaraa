from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HudsonLoan(models.Model):
    _name = 'hudson.loan'
    _description = 'Loan Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    amount_borrowed = fields.Monetary(string='Amount Borrowed', required=True, tracking=True)
    interest = fields.Monetary(string='Interest', compute='_compute_totals', store=True)
    outstanding_balance = fields.Monetary(string='Outstanding Balance', compute='_compute_totals', store=True)
    
    date = fields.Date(string='Loan Date', required=True, default=fields.Date.context_today)
    duration = fields.Integer(string='Duration (months)', required=True, default=12)
    asset_group = fields.Char(string='Asset Group')
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Amortization Schedule
    line_ids = fields.One2many('hudson.loan.line', 'loan_id', string='Amortization Schedule')
    
    # Loan Settings
    long_term_account_id = fields.Many2one('account.account', string='Long Term Account', required=True)
    short_term_account_id = fields.Many2one('account.account', string='Short Term Account', required=True)
    expense_account_id = fields.Many2one('account.account', string='Expense Account', required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    skip_until_date = fields.Date(
        string='Skip until',
        help="Upon confirmation of the loan, Odoo will ignore the loan lines that are up to this date (included) and not create entries for them. This is useful if you have already manually created entries prior to the creation of this loan."
    )
    receive_disbursement = fields.Boolean(string='Create Disbursement Entry', default=False)
    disbursement_account_id = fields.Many2one('account.account', string='Disbursement Account (Bank)')
    
    # Posted Entries
    move_ids = fields.One2many('account.move', 'hudson_loan_id', string='Loan Entries')
    move_count = fields.Integer(compute='_compute_move_count')

    @api.depends('line_ids.principal', 'line_ids.interest', 'line_ids.balance', 'line_ids.is_posted')
    def _compute_totals(self):
        for loan in self:
            loan.interest = sum(loan.line_ids.mapped('interest'))
            if loan.line_ids:
                # Outstanding balance is the amount borrowed minus the sum of posted/skipped principal payments
                posted_principal = sum(loan.line_ids.filtered(lambda l: l.is_posted).mapped('principal'))
                loan.outstanding_balance = loan.amount_borrowed - posted_principal
            else:
                loan.outstanding_balance = loan.amount_borrowed

    @api.depends('move_ids')
    def _compute_move_count(self):
        for loan in self:
            loan.move_count = len(loan.move_ids)
            
    def action_compute(self):
        self.ensure_one()
        return {
            'name': _('Compute New Loan'),
            'type': 'ir.actions.act_window',
            'res_model': 'hudson.loan.compute.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_loan_id': self.id,
                'default_amount': self.amount_borrowed,
                'default_start_date': self.date or fields.Date.context_today(self),
                'default_term_years': max(1, self.duration // 12) if self.duration else 1,
            }
        }

    def action_confirm(self):
        self.ensure_one()
        if not self.long_term_account_id or not self.short_term_account_id or not self.expense_account_id or not self.journal_id:
            raise UserError(_("Please configure the Loan Settings accounts and Journal before confirming."))
            
        if not self.line_ids:
            raise UserError(_("Please compute the amortization schedule before confirming."))
            
        # Amortization Installment Entries
        for line in self.line_ids:
            if self.skip_until_date and line.date <= self.skip_until_date:
                continue
                
            move_vals = {
                'date': line.date,
                'journal_id': self.journal_id.id,
                'hudson_loan_id': self.id,
                'ref': f"{self.name} - Principal & Interest {line.date.strftime('%m/%Y')}",
                'auto_post': 'at_date',
                'line_ids': [
                    (0, 0, {
                        'name': 'Principal Repayment',
                        'account_id': self.long_term_account_id.id,
                        'debit': line.principal,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': 'Interest Expense',
                        'account_id': self.expense_account_id.id,
                        'debit': line.interest,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': 'Bank/Liability',
                        'account_id': self.short_term_account_id.id,
                        'debit': 0.0,
                        'credit': line.principal + line.interest,
                    }),
                ]
            }
            move = self.env['account.move'].create(move_vals)
            line.move_id = move.id
            
        self.state = 'running'

    def action_cancel(self):
        for loan in self:
            unposted_moves = loan.move_ids.filtered(lambda m: m.state == 'draft')
            unposted_moves.button_cancel()
            unposted_moves.unlink()
            loan.state = 'cancelled'

    def action_reset_to_draft(self):
        for loan in self:
            posted_moves = loan.move_ids.filtered(lambda m: m.state == 'posted')
            if posted_moves:
                raise UserError(_("Cannot reset to draft while posted entries exist. Please cancel or reverse posted entries first."))
            unposted_moves = loan.move_ids.filtered(lambda m: m.state == 'draft')
            unposted_moves.unlink()
            loan.state = 'draft'

    def action_close(self):
        for loan in self:
            loan.state = 'closed'

    def action_view_entries(self):
        self.ensure_one()
        return {
            'name': _('Loan Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('hudson_loan_id', '=', self.id)],
            'context': dict(self._context, create=False),
        }

class HudsonLoanLine(models.Model):
    _name = 'hudson.loan.line'
    _description = 'Loan Amortization Line'
    _order = 'date asc'

    loan_id = fields.Many2one('hudson.loan', string='Loan', ondelete='cascade')
    date = fields.Date(string='Date', required=True)
    principal = fields.Monetary(string='Principals', currency_field='currency_id')
    interest = fields.Monetary(string='Interests', currency_field='currency_id')
    payment = fields.Monetary(string='Payments', currency_field='currency_id')
    balance = fields.Monetary(string='Outstanding Balance', currency_field='currency_id')
    
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    is_posted = fields.Boolean(string='Posted', compute='_compute_is_posted', store=True)
    
    @api.depends('move_id.state', 'loan_id.skip_until_date', 'loan_id.state', 'date')
    def _compute_is_posted(self):
        for line in self:
            if line.move_id and line.move_id.state == 'posted':
                line.is_posted = True
            elif line.loan_id.skip_until_date and line.date and line.date <= line.loan_id.skip_until_date and line.loan_id.state in ('running', 'closed'):
                line.is_posted = True
            else:
                line.is_posted = False
    
    currency_id = fields.Many2one(related='loan_id.currency_id', depends=['loan_id.currency_id'])

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    hudson_loan_id = fields.Many2one('hudson.loan', string='Loan Reference')
