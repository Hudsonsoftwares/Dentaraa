from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountUnrealizedCurrencyWizard(models.TransientModel):
    """
    Unrealized Currency Gains/Losses Report.

    For each open receivable/payable in a foreign currency, computes:
    - Original amount in company currency (at transaction date rate)
    - Current value in company currency (at today's/selected rate)
    - Unrealized Gain or Loss = Current Value - Original Value

    Positive = Unrealized Gain, Negative = Unrealized Loss.

    Uses: account.move.line with reconciled=False on receivable/payable accounts
    where currency_id != company currency_id.
    """
    _name = 'account.unrealized.currency.wizard'
    _description = 'Unrealized Currency Gains/Losses'

    as_of_date = fields.Date(
        string='As Of Date',
        required=True,
        default=lambda self: date.today(),
        help='Compute unrealized gains/losses using exchange rates as of this date.',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    target_move = fields.Selection(
        [('posted', 'All Posted Entries'), ('all', 'All Entries')],
        string='Target Moves',
        required=True,
        default='posted',
    )

    def _get_currency_rate(self, currency, as_of_date, company):
        """Get the exchange rate for a currency as of a given date."""
        if currency == company.currency_id:
            return 1.0
        rate_record = self.env['res.currency.rate'].search([
            ('currency_id', '=', currency.id),
            ('name', '<=', as_of_date),
            ('company_id', '=', company.id),
        ], order='name desc', limit=1)
        if rate_record and rate_record.rate:
            # Odoo rate: amount of foreign per 1 company_currency
            # To get company_currency per 1 foreign: 1 / rate
            return 1.0 / rate_record.rate
        return 1.0

    def _compute_unrealized_data(self):
        self.ensure_one()
        company = self.company_id
        as_of = self.as_of_date

        domain = [
            ('company_id', '=', company.id),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
            ('reconciled', '=', False),
            ('currency_id', '!=', company.currency_id.id),
            ('currency_id', '!=', False),
            ('date', '<=', as_of),
        ]
        
        if self.target_move == 'posted':
            domain.append(('parent_state', '=', 'posted'))

        # Get all unreconciled move lines in foreign currencies on AR/AP accounts
        lines = self.env['account.move.line'].search(domain)

        # Group by currency
        by_currency = {}
        for line in lines:
            curr = line.currency_id
            if curr not in by_currency:
                by_currency[curr] = {
                    'currency': curr,
                    'lines': [],
                }
            by_currency[curr]['lines'].append(line)

        results = []
        total_unrealized = 0.0

        for curr, group in by_currency.items():
            # Get current rate (1 foreign = X company_currency)
            current_rate = self._get_currency_rate(curr, as_of, company)

            currency_result = {
                'currency_name': curr.name,
                'currency_symbol': curr.symbol,
                'items': [],
                'total_original': 0.0,
                'total_current': 0.0,
                'total_gain_loss': 0.0,
            }

            for line in group['lines']:
                # Original amount in company currency (as recorded at transaction)
                original_company = line.debit - line.credit  # positive for AR, negative for AP

                # Amount in foreign currency
                amount_foreign = line.amount_currency  # signed

                # Current value in company currency at today's rate
                current_company = amount_foreign * current_rate

                # Unrealized gain/loss
                unrealized = current_company - original_company

                currency_result['items'].append({
                    'partner': line.partner_id.name or '',
                    'date': line.date,
                    'ref': line.move_id.name or line.name or '',
                    'account': f"{line.account_id.code} {line.account_id.name}",
                    'amount_foreign': amount_foreign,
                    'original_company': original_company,
                    'current_rate': round(current_rate, 6),
                    'current_company': current_company,
                    'unrealized': unrealized,
                })

                currency_result['total_original'] += original_company
                currency_result['total_current'] += current_company
                currency_result['total_gain_loss'] += unrealized

            total_unrealized += currency_result['total_gain_loss']
            results.append(currency_result)

        return {
            'as_of_date': as_of,
            'company': company.id,
            'results': results,
            'total_unrealized': total_unrealized,
        }

    def action_print_report(self):
        self.ensure_one()
        data = self._compute_unrealized_data()
        return self.env.ref(
            'hudson_accounting_enhancements.action_report_unrealized_currency'
        ).report_action(self, data={'form': data})

    def check_report(self):
        return self.action_print_report()


from dateutil.relativedelta import relativedelta


class AccountUnrealizedCurrencyAdjustmentWizard(models.TransientModel):
    _name = 'account.unrealized.currency.adjustment.wizard'
    _description = 'Make Adjustment Entry'

    def _default_journal(self):
        company = self.env.company
        return (
            self.env['account.journal'].search([('company_id', '=', company.id), ('code', '=', 'EXCH')], limit=1)
            or self.env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'general')], limit=1)
        )

    def _default_expense_account(self):
        company = self.env.company
        return (
            company.expense_currency_exchange_account_id
            or self.env['account.account'].search([('account_type', '=', 'expense')], limit=1)
        )

    def _default_income_account(self):
        company = self.env.company
        return (
            company.income_currency_exchange_account_id
            or self.env['account.account'].search([('account_type', '=', 'income_other')], limit=1)
            or self.env['account.account'].search([('account_type', '=', 'income')], limit=1)
        )

    def _default_reversal_date(self):
        today = fields.Date.context_today(self)
        return today + relativedelta(days=1)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
        default=_default_journal,
    )
    expense_account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        required=True,
        check_company=True,
        domain="[('account_type', '=', 'expense')]",
        default=_default_expense_account,
    )
    income_account_id = fields.Many2one(
        'account.account',
        string='Income Account',
        required=True,
        check_company=True,
        domain="[('account_type', 'in', ['income', 'income_other'])]",
        default=_default_income_account,
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
    )
    reversal_date = fields.Date(
        string='Reversal Date',
        default=_default_reversal_date,
    )
    header_note = fields.Char(string='Section Note', compute='_compute_header_note')
    line_ids = fields.One2many(
        'account.unrealized.currency.adjustment.line',
        'wizard_id',
        string='Adjustment Lines',
        compute='_compute_lines',
        readonly=False,
    )

    @api.depends('date')
    def _compute_header_note(self):
        for wiz in self:
            if wiz.date:
                df = wiz.date.strftime('%d/%m/%Y')
                wiz.header_note = f"{df}, Foreign currencies adjustment entry as of {df}"
            else:
                wiz.header_note = ''

    @api.depends('date', 'company_id', 'expense_account_id', 'income_account_id')
    def _compute_lines(self):
        for wiz in self:
            if not wiz.date or not wiz.company_id:
                wiz.line_ids = [(5, 0, 0)]
                continue

            company = wiz.company_id
            as_of = wiz.date
            domain = [
                ('company_id', '=', company.id),
                ('date', '<=', as_of),

                ('reconciled', '=', False),
                ('currency_id', '!=', False),
                ('currency_id', '!=', company.currency_id.id),
                ('account_id.account_type', 'in', [
                    'asset_receivable', 'liability_payable',
                    'asset_current', 'liability_current',
                    'asset_prepayments', 'liability_credit_card',
                    'asset_non_current', 'liability_non_current',
                    'asset_cash'
                ])
            ]
            lines = self.env['account.move.line'].search(domain)

            acc_currency_data = {}
            for l in lines:
                curr = l.currency_id
                acc = l.account_id
                key = (curr, acc)
                if key not in acc_currency_data:
                    rate_rec = self.env['res.currency.rate'].search([
                        ('currency_id', '=', curr.id),
                        ('name', '<=', as_of),
                        ('company_id', '=', company.id),
                    ], order='name desc', limit=1)
                    curr_rate = rate_rec.rate if (rate_rec and rate_rec.rate) else (curr.rate or 1.0)
                    acc_currency_data[key] = {
                        'currency': curr,
                        'account': acc,
                        'rate': curr_rate,
                        'adj_total': 0.0,
                    }

                foreign_amt = l.amount_residual_currency or l.amount_currency or 0.0
                if abs(foreign_amt) < 0.0001:
                    continue
                op_bal = l.amount_residual if l.amount_residual else (l.debit - l.credit)
                curr_bal = curr._convert(foreign_amt, company.currency_id, company, as_of)
                adj = curr_bal - op_bal
                acc_currency_data[key]['adj_total'] += adj

            new_lines = []
            for (curr, acc), data in acc_currency_data.items():
                adj = round(data['adj_total'], 2)
                if abs(adj) < 0.005:
                    continue
                curr_rate = data['rate']
                rate_str = f"Provision for {curr.name} (1 {company.currency_id.name} = {curr_rate:.17g} {curr.name})"

                if adj < 0:
                    loss_amt = abs(adj)
                    new_lines.append((0, 0, {
                        'account_id': acc.id,
                        'name': rate_str,
                        'debit': 0.0,
                        'credit': loss_amt,
                        'currency_id': company.currency_id.id,
                    }))
                    dest_acc = wiz.expense_account_id or acc
                    new_lines.append((0, 0, {
                        'account_id': dest_acc.id,
                        'name': f"Expense Provision for {curr.name}",
                        'debit': loss_amt,
                        'credit': 0.0,
                        'currency_id': company.currency_id.id,
                    }))
                else:
                    gain_amt = adj
                    new_lines.append((0, 0, {
                        'account_id': acc.id,
                        'name': rate_str,
                        'debit': gain_amt,
                        'credit': 0.0,
                        'currency_id': company.currency_id.id,
                    }))
                    dest_acc = wiz.income_account_id or acc
                    new_lines.append((0, 0, {
                        'account_id': dest_acc.id,
                        'name': f"Income Provision for {curr.name}",
                        'debit': 0.0,
                        'credit': gain_amt,
                        'currency_id': company.currency_id.id,
                    }))

            wiz.line_ids = [(5, 0, 0)] + new_lines

    def action_create_entry(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("There are no adjustment lines to create an entry for."))

        move_vals = {
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'date': self.date,
            'ref': f"Foreign currencies adjustment entry as of {self.date.strftime('%d/%m/%Y')}",
            'line_ids': [
                (0, 0, {
                    'account_id': l.account_id.id,
                    'name': l.name or '/',
                    'debit': l.debit,
                    'credit': l.credit,
                    'currency_id': self.company_id.currency_id.id,
                }) for l in self.line_ids
            ]
        }
        if self.reversal_date:
            move_vals['auto_post'] = 'no'

        move = self.env['account.move'].create(move_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Adjustment Entry'),
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'views': [[False, 'form']],
        }


class AccountUnrealizedCurrencyAdjustmentLine(models.TransientModel):
    _name = 'account.unrealized.currency.adjustment.line'
    _description = 'Adjustment Entry Line'

    wizard_id = fields.Many2one('account.unrealized.currency.adjustment.wizard', ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Account', required=True)
    name = fields.Char(string='Label', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    debit = fields.Monetary(string='Debit', currency_field='currency_id')
    credit = fields.Monetary(string='Credit', currency_field='currency_id')

