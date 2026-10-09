from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_dental_clinic = fields.Boolean(
        string='Is a Dental Clinic',
        default=True,
        help='Check if this company/branch operates as a dental clinic.',
    )
    clinic_manager_id = fields.Many2one(
        'hr.employee',
        string='Clinic Manager / Head Doctor',
    )
    opening_time = fields.Float(string='Opening Time', default=9.0)
    closing_time = fields.Float(string='Closing Time', default=20.0)
    working_days = fields.Char(string='Working Days', default='Monday - Saturday')
    clinic_registration_number = fields.Char(string='Clinic Reg. No.')
    letterhead_header = fields.Html(string='Letterhead Header')
    letterhead_footer = fields.Html(string='Letterhead Footer')
    clinic_notes = fields.Text(string='Internal Notes')
