from odoo import api, models, _
from odoo.exceptions import UserError


class ReportAnnual(models.AbstractModel):
    _name = 'report.hudson_accounting_enhancements.report_annual'
    _description = 'Annual Financial Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data or not data.get('form'):
            raise UserError(_('Annual Report data is missing. Please use the wizard.'))
        form = data['form']
        company_data = form.get('company')
        if isinstance(company_data, (list, tuple)):
            company = self.env['res.company'].browse(company_data[0])
        else:
            company = self.env['res.company'].browse(company_data)

        # Make logo available as base64 string for template
        logo_b64 = False
        if company.logo:
            try:
                logo_b64 = company.logo.decode('utf-8')
            except Exception:
                logo_b64 = False

        return {
            'doc_ids': docids,
            'doc_model': 'account.annual.report.wizard',
            'data': form,
            'company': company,
            'currency': company.currency_id,
            'logo_b64': logo_b64,
        }
