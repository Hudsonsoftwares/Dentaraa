from odoo import models, fields

class DentalDiagnosisMaster(models.Model):
    _name = 'dental.diagnosis'
    _description = 'Diagnosis Master'

    name = fields.Char(string='Diagnosis Name', required=True)
    code = fields.Char(string='Diagnosis Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)

class DentalPatientDiagnosis(models.Model):
    _name = 'dental.patient.diagnosis'
    _description = 'Patient Diagnosis'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    case_id = fields.Many2one('dental.case', string='Dental Case', tracking=True)
    examination_id = fields.Many2one('dental.clinical.examination', string='Examination', tracking=True)
    doctor_id = fields.Many2one('hr.employee', string='Doctor', tracking=True)
    diagnosis_id = fields.Many2one('dental.diagnosis', string='Diagnosis', required=True, tracking=True)
    notes = fields.Text(string='Notes')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    status = fields.Selection([
        ('suspected', 'Suspected'),
        ('confirmed', 'Confirmed'),
        ('resolved', 'Resolved')
    ], string='Status', default='confirmed', tracking=True)
