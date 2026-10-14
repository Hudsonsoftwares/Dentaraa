from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAnnualReport(models.Model):
    """
    Persistent Annual Report record — stores each annual report with its own
    date range, responsible users, and company. Reports can be printed at any time.
    """
    _name = 'account.annual.report'
    _description = 'Annual Report'
    _order = 'date_to desc, id desc'

    name = fields.Char(
        string='Title',
        required=True,
        placeholder='e.g. Annual Financial Overview',
    )

    date_from = fields.Date(
        string='Date From',
        required=True,
        default=lambda self: date.today().replace(month=1, day=1),
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        default=lambda self: date.today().replace(month=12, day=31),
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
        required=True,
        default=lambda self: self.env.company,
    )
    user_ids = fields.Many2many(
        'res.users',
        string='Responsibles',
        default=lambda self: self.env.user,
    )
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed')],
        string='Status',
        default='draft',
        readonly=True,
    )

    # ──────────────────────────────────────────────────────
    # Data Computation Helpers
    # ──────────────────────────────────────────────────────

    def _get_balance(self, account_types, date_from, date_to, company_id, state):
        """Period movement balance for P&L items."""
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
        """Cumulative balance up to date for BS items."""
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

    def _get_prior_year_balance(self, account_types, as_of_date, company_id, state):
        """Get balance as of one year before (prior year comparison)."""
        from datetime import timedelta
        prior_date = as_of_date.replace(year=as_of_date.year - 1)
        return self._get_cumulative_balance(account_types, prior_date, company_id, state)

    def _get_prior_year_period_balance(self, account_types, date_from, date_to, company_id, state):
        """Prior year period movement balance."""
        try:
            prior_from = date_from.replace(year=date_from.year - 1)
            prior_to = date_to.replace(year=date_to.year - 1)
        except ValueError:
            # Feb 29 edge case
            prior_from = date_from.replace(year=date_from.year - 1, day=28)
            prior_to = date_to.replace(year=date_to.year - 1, day=28)
        return self._get_balance(account_types, prior_from, prior_to, company_id, state)

    def _get_aged_lines(self, account_type, as_of_date, company_id, state, period_length=30):
        """Get aged payable/receivable bucket totals."""
        state_clause = "AND am.state = 'posted'" if state == 'posted' else ''
        query = f"""
            SELECT
                COALESCE(SUM(aml.amount_residual), 0) as total,
                COALESCE(SUM(CASE WHEN (%(as_of)s - COALESCE(aml.date_maturity, aml.date)) BETWEEN 1 AND %(p)s THEN aml.amount_residual ELSE 0 END), 0) as b1,
                COALESCE(SUM(CASE WHEN (%(as_of)s - COALESCE(aml.date_maturity, aml.date)) BETWEEN %(p)s+1 AND %(p2)s THEN aml.amount_residual ELSE 0 END), 0) as b2,
                COALESCE(SUM(CASE WHEN (%(as_of)s - COALESCE(aml.date_maturity, aml.date)) BETWEEN %(p2)s+1 AND %(p3)s THEN aml.amount_residual ELSE 0 END), 0) as b3,
                COALESCE(SUM(CASE WHEN (%(as_of)s - COALESCE(aml.date_maturity, aml.date)) BETWEEN %(p3)s+1 AND %(p4)s THEN aml.amount_residual ELSE 0 END), 0) as b4,
                COALESCE(SUM(CASE WHEN (%(as_of)s - COALESCE(aml.date_maturity, aml.date)) > %(p4)s THEN aml.amount_residual ELSE 0 END), 0) as b5,
                COALESCE(SUM(CASE WHEN (%(as_of)s - COALESCE(aml.date_maturity, aml.date)) <= 0 THEN aml.amount_residual ELSE 0 END), 0) as current_amt
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move am ON am.id = aml.move_id
            WHERE aa.account_type = %(atype)s
              AND aml.date <= %(as_of)s
              AND aml.company_id = %(cid)s
              AND aml.display_type NOT IN ('line_section', 'line_note')
              AND aml.amount_residual != 0
              {state_clause}
        """
        self.env.cr.execute(query, {
            'as_of': as_of_date,
            'atype': account_type,
            'cid': company_id,
            'p': period_length,
            'p2': period_length * 2,
            'p3': period_length * 3,
            'p4': period_length * 4,
        })
        row = self.env.cr.fetchone()
        if row:
            return {
                'total': row[0], 'b1': row[1], 'b2': row[2],
                'b3': row[3], 'b4': row[4], 'b5': row[5], 'current': row[6],
            }
        return {'total': 0, 'b1': 0, 'b2': 0, 'b3': 0, 'b4': 0, 'b5': 0, 'current': 0}

    def _compute_annual_data(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_('Date From must be before Date To.'))

        cid = self.company_id.id
        df = self.date_from
        dt = self.date_to
        st = self.target_move

        # ── P&L (current period) ──
        revenue = -self._get_balance(['income'], df, dt, cid, st)
        other_income = -self._get_balance(['income_other'], df, dt, cid, st)
        cogs = self._get_balance(['expense_direct_cost'], df, dt, cid, st)
        operating_expenses = self._get_balance(['expense'], df, dt, cid, st)
        depreciation = self._get_balance(['expense_depreciation'], df, dt, cid, st)
        gross_profit = revenue - cogs
        operating_profit = gross_profit - operating_expenses - depreciation
        net_profit = operating_profit + other_income

        # ── P&L (prior period) ──
        prev_revenue = -self._get_prior_year_period_balance(['income'], df, dt, cid, st)
        prev_other_income = -self._get_prior_year_period_balance(['income_other'], df, dt, cid, st)
        prev_cogs = self._get_prior_year_period_balance(['expense_direct_cost'], df, dt, cid, st)
        prev_operating_expenses = self._get_prior_year_period_balance(['expense'], df, dt, cid, st)
        prev_depreciation = self._get_prior_year_period_balance(['expense_depreciation'], df, dt, cid, st)
        prev_gross_profit = prev_revenue - prev_cogs
        prev_net_profit = prev_gross_profit + prev_other_income - prev_operating_expenses - prev_depreciation

        # ── Balance Sheet (current) ──
        cash = self._get_cumulative_balance(['asset_cash'], dt, cid, st)
        receivables = self._get_cumulative_balance(['asset_receivable'], dt, cid, st)
        current_assets = self._get_cumulative_balance(['asset_current'], dt, cid, st)
        prepayments = self._get_cumulative_balance(['asset_prepayments'], dt, cid, st)
        fixed_assets = self._get_cumulative_balance(['asset_fixed'], dt, cid, st)
        noncurrent_assets = self._get_cumulative_balance(['asset_non_current'], dt, cid, st)
        total_current_assets = cash + receivables + current_assets + prepayments
        total_assets = total_current_assets + fixed_assets + noncurrent_assets

        curr_liab = -self._get_cumulative_balance(['liability_current'], dt, cid, st)
        credit_card = -self._get_cumulative_balance(['liability_credit_card'], dt, cid, st)
        payables = -self._get_cumulative_balance(['liability_payable'], dt, cid, st)
        total_curr_liab = curr_liab + credit_card + payables
        noncurrent_liab = -self._get_cumulative_balance(['liability_non_current'], dt, cid, st)
        total_liabilities = total_curr_liab + noncurrent_liab

        equity = -self._get_cumulative_balance(['equity'], dt, cid, st)
        unallocated_earnings = -self._get_cumulative_balance(['equity_unaffected'], dt, cid, st)
        total_equity = equity + unallocated_earnings + net_profit

        # ── Balance Sheet (prior year) ──
        prior_dt = dt.replace(year=dt.year - 1)
        p_cash = self._get_cumulative_balance(['asset_cash'], prior_dt, cid, st)
        p_receivables = self._get_cumulative_balance(['asset_receivable'], prior_dt, cid, st)
        p_current_assets = self._get_cumulative_balance(['asset_current'], prior_dt, cid, st)
        p_prepayments = self._get_cumulative_balance(['asset_prepayments'], prior_dt, cid, st)
        p_fixed_assets = self._get_cumulative_balance(['asset_fixed'], prior_dt, cid, st)
        p_noncurrent_assets = self._get_cumulative_balance(['asset_non_current'], prior_dt, cid, st)
        p_total_current_assets = p_cash + p_receivables + p_current_assets + p_prepayments
        p_total_assets = p_total_current_assets + p_fixed_assets + p_noncurrent_assets

        p_curr_liab = -self._get_cumulative_balance(['liability_current'], prior_dt, cid, st)
        p_credit_card = -self._get_cumulative_balance(['liability_credit_card'], prior_dt, cid, st)
        p_payables = -self._get_cumulative_balance(['liability_payable'], prior_dt, cid, st)
        p_total_curr_liab = p_curr_liab + p_credit_card + p_payables
        p_noncurrent_liab = -self._get_cumulative_balance(['liability_non_current'], prior_dt, cid, st)
        p_total_liabilities = p_total_curr_liab + p_noncurrent_liab
        p_equity = -self._get_cumulative_balance(['equity'], prior_dt, cid, st)
        p_unallocated = -self._get_cumulative_balance(['equity_unaffected'], prior_dt, cid, st)
        p_total_equity = p_equity + p_unallocated + prev_net_profit

        # ── Aged ──
        aged_payable = self._get_aged_lines('liability_payable', dt, cid, st)
        aged_receivable = self._get_aged_lines('asset_receivable', dt, cid, st)

        return {
            # meta
            'report_name': self.name,
            'date_from': df,
            'date_to': dt,
            'prior_date_to': prior_dt,
            'company_id': cid,
            'target_move': st,
            # P&L current
            'revenue': revenue, 'other_income': other_income,
            'cogs': cogs, 'operating_expenses': operating_expenses,
            'depreciation': depreciation, 'gross_profit': gross_profit,
            'operating_profit': operating_profit, 'net_profit': net_profit,
            # P&L prior
            'prev_revenue': prev_revenue, 'prev_other_income': prev_other_income,
            'prev_cogs': prev_cogs, 'prev_operating_expenses': prev_operating_expenses,
            'prev_depreciation': prev_depreciation, 'prev_gross_profit': prev_gross_profit,
            'prev_net_profit': prev_net_profit,
            # BS current
            'cash': cash, 'receivables': receivables, 'current_assets': current_assets,
            'prepayments': prepayments, 'fixed_assets': fixed_assets,
            'noncurrent_assets': noncurrent_assets,
            'total_current_assets': total_current_assets, 'total_assets': total_assets,
            'curr_liab': curr_liab, 'credit_card': credit_card, 'payables': payables,
            'total_curr_liab': total_curr_liab, 'noncurrent_liab': noncurrent_liab,
            'total_liabilities': total_liabilities,
            'equity': equity, 'unallocated_earnings': unallocated_earnings,
            'total_equity': total_equity,
            # BS prior
            'p_cash': p_cash, 'p_receivables': p_receivables,
            'p_current_assets': p_current_assets, 'p_prepayments': p_prepayments,
            'p_fixed_assets': p_fixed_assets, 'p_noncurrent_assets': p_noncurrent_assets,
            'p_total_current_assets': p_total_current_assets, 'p_total_assets': p_total_assets,
            'p_curr_liab': p_curr_liab, 'p_credit_card': p_credit_card, 'p_payables': p_payables,
            'p_total_curr_liab': p_total_curr_liab, 'p_noncurrent_liab': p_noncurrent_liab,
            'p_total_liabilities': p_total_liabilities,
            'p_equity': p_equity, 'p_unallocated': p_unallocated, 'p_total_equity': p_total_equity,
            # Aged
            'aged_payable': aged_payable,
            'aged_receivable': aged_receivable,
        }

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref(
            'hudson_accounting_enhancements.action_report_annual'
        ).report_action(self)

    def check_report(self):
        return self.action_print_report()
