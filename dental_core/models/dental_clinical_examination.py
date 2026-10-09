from odoo import models, fields, api, _

class DentalClinicalExamination(models.Model):
    _name = 'dental.clinical.examination'
    _description = 'Clinical Examination'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Examination Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    case_id = fields.Many2one('dental.case', string='Dental Case', required=True, tracking=True)
    doctor_id = fields.Many2one('hr.employee.public', string='Doctor', tracking=True)
    examination_date = fields.Datetime(string='Examination Date', default=fields.Datetime.now, required=True, tracking=True)
    
    chief_complaint = fields.Text(string='Chief Complaint')
    presenting_complaint = fields.Text(string='Presenting Complaint')
    
    # Dental Observations
    oral_hygiene = fields.Selection([
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string='Oral Hygiene')
    gum_condition = fields.Char(string='Gum Condition')
    tooth_condition_summary = fields.Text(string='Tooth Condition Summary')
    soft_tissue_findings = fields.Text(string='Soft Tissue Findings')
    occlusion = fields.Char(string='Occlusion')
    clinical_findings = fields.Text(string='Clinical Findings')
    additional_notes = fields.Text(string='Additional Notes')
    
    # Vitals
    height = fields.Float(string='Height (cm)')
    weight = fields.Float(string='Weight (kg)')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)
    temperature = fields.Float(string='Temperature (°C)')
    blood_pressure = fields.Char(string='Blood Pressure (mmHg)')
    pulse_rate = fields.Integer(string='Pulse Rate (bpm)')
    respiratory_rate = fields.Integer(string='Respiratory Rate (bpm)')
    oxygen_saturation = fields.Float(string='Oxygen Saturation (%)')

    @api.depends('height', 'weight')
    def _compute_bmi(self):
        for rec in self:
            if rec.height > 0 and rec.weight > 0:
                height_m = rec.height / 100.0
                rec.bmi = rec.weight / (height_m * height_m)
            else:
                rec.bmi = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.clinical.examination') or _('New')
        return super().create(vals_list)
