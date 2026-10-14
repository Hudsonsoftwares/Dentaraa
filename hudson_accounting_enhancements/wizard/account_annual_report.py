from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAnnualReportWizard(models.TransientModel):
    """
    Annual Report wizard — combines the Balance Sheet and P&L for a full fiscal year
    into a single comprehensive financial summary document.
    """
    _name = 'account.annual.report.wizard'
    _description = 'Annual Financial Report'

    fiscal_year = fields.Integer(
        string='Fiscal Year',
        required=True,
        default=lambda self: date.today().year - 1,
    )
    date_from = fields.Date(
        string='Date From',
        required=True,
        default=lambda self: date.today().replace(month=1, day=1, year=date.today().year - 1),
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        default=lambda self: date.today().replace(month=12, day=31, year=date.today().year - 1),
    )
    target_move = fields.Selection(
        [('posted', 'All Posted Entries'), ('all', 'All Entries')],
        string='Target Moves',
        required=True,
        default='posted',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    @api.onchange('fiscal_year')
    def _onchange_fiscal_year(self):
        if self.fiscal_year:
            self.date_from = date(self.fiscal_year, 1, 1)
            self.date_to = date(self.fiscal_year, 12, 31)

    def _get_balance(self, account_types, date_from, date_to, company_id, state):
        """Get net debit-credit balance for given account types in a period."""
        state_clause = "AND aml.parent_state = 'posted'" if state == 'posted' else ''
        query = f"""
            SELECT COALESCE(SUM(aml.debit - aml.credit), 0.0)
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE aa.account_type IN %s
              AND aml.date >= %s
              AND aml.date <= %s
              AND aml.company_id = %s
              AND aml.display_type NOT IN ('line_section', 'line_note')
              {state_clause}
        """
        self.env.cr.execute(query, (tuple(account_types), date_from, date_to, company_id))
        result = self.env.cr.fetchone()
        return result[0] if result else 0.0

    def _get_cumulative_balance(self, account_types, as_of_date, company_id, state):
        """Get cumulative balance up to a date for BS items."""
        state_clause = "AND aml.parent_state = 'posted'" if state == 'posted' else ''
        query = f"""
            SELECT COALESCE(SUM(aml.debit - aml.credit), 0.0)
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE aa.account_type IN %s
              AND aml.date <= %s
              AND aml.company_id = %s
              AND aml.display_type NOT IN ('line_section', 'line_note')
              {state_clause}
        """
        self.env.cr.execute(query, (tuple(account_types), as_of_date, company_id))
        result = self.env.cr.fetchone()
        return result[0] if result else 0.0

    def _compute_annual_data(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_('Date From must be before Date To.'))

        cid = self.company_id.id
        df = self.date_from
        dt = self.date_to
        st = self.target_move

        # ── P&L Items (period movements) ──
        revenue = -self._get_balance(['income'], df, dt, cid, st)
        other_income = -self._get_balance(['income_other'], df, dt, cid, st)
        cogs = self._get_balance(['expense_direct_cost'], df, dt, cid, st)
        operating_expenses = self._get_balance(['expense'], df, dt, cid, st)
        depreciation = self._get_balance(['expense_depreciation'], df, dt, cid, st)

        gross_profit = revenue - cogs
        operating_profit = gross_profit - operating_expenses - depreciation
        net_profit = operating_profit + other_income

        # ── Balance Sheet Items (cumulative as of date_to) ──
        # Assets
        current_assets = self._get_cumulative_balance(
            ['asset_receivable', 'asset_cash', 'asset_current', 'asset_prepayments'], dt, cid, st
        )
        noncurrent_assets = self._get_cumulative_balance(
            ['asset_non_current', 'asset_fixed'], dt, cid, st
        )
        total_assets = current_assets + noncurrent_assets

        # Liabilities
        current_liabilities = -self._get_cumulative_balance(
            ['liability_payable', 'liability_credit_card', 'liability_current'], dt, cid, st
        )
        noncurrent_liabilities = -self._get_cumulative_balance(
            ['liability_non_current'], dt, cid, st
        )
        total_liabilities = current_liabilities + noncurrent_liabilities

        # Equity
        share_capital = -self._get_cumulative_balance(['equity'], dt, cid, st)
        retained_earnings = -self._get_cumulative_balance(['equity_unaffected'], dt, cid, st)
        total_equity = share_capital + retained_earnings + net_profit

        return {
            'fiscal_year': self.fiscal_year,
            'date_from': df,
            'date_to': dt,
            'company': self.company_id.id,
            'target_move': st,
            # P&L
            'revenue': revenue,
            'other_income': other_income,
            'cogs': cogs,
            'gross_profit': gross_profit,
            'operating_expenses': operating_expenses,
            'depreciation': depreciation,
            'operating_profit': operating_profit,
            'net_profit': net_profit,
            # BS
            'current_assets': current_assets,
            'noncurrent_assets': noncurrent_assets,
            'total_assets': total_assets,
            'current_liabilities': current_liabilities,
            'noncurrent_liabilities': noncurrent_liabilities,
            'total_liabilities': total_liabilities,
            'share_capital': share_capital,
            'retained_earnings': retained_earnings,
            'total_equity': total_equity,
        }

    def action_print_report(self):
        self.ensure_one()
        data = self._compute_annual_data()
        return self.env.ref(
            'hudson_accounting_enhancements.action_report_annual'
        ).report_action(self, data={'form': data})

    def check_report(self):
        return self.action_print_report()
