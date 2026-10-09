from odoo import models, fields, api, _

class DentalCase(models.Model):
    _name = 'dental.case'
    _description = 'Dental Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Case Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    doctor_id = fields.Many2one('hr.employee', string='Doctor', tracking=True)
    appointment_id = fields.Many2one('dental.appointment', string='Related Appointment', tracking=True)
    branch_id = fields.Many2one('res.company', string='Branch', related='appointment_id.branch_id', store=True)
    
    case_date = fields.Date(string='Case Date', default=fields.Date.context_today, required=True, tracking=True)
    
    chief_complaint = fields.Text(string='Chief Complaint')
    clinical_notes = fields.Text(string='Clinical Notes')
    
    medical_history_summary = fields.Text(string='Medical History Summary')
    dental_history_summary = fields.Text(string='Dental History Summary')
    allergies = fields.Text(string='Allergies')
    current_medications = fields.Text(string='Current Medications')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('under_treatment', 'Under Treatment'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Case Status', default='draft', tracking=True)
    
    examination_ids = fields.One2many('dental.clinical.examination', 'case_id', string='Examinations')
    diagnosis_ids = fields.One2many('dental.patient.diagnosis', 'case_id', string='Diagnoses')
    treatment_plan_ids = fields.One2many('dental.treatment.plan', 'case_id', string='Treatment Plans')
    treatment_session_ids = fields.One2many('dental.treatment.session', 'case_id', string='Treatment Sessions')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.case') or _('New')
        return super().create(vals_list)

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            self.medical_history_summary = self.patient_id.existing_conditions
            self.allergies = self.patient_id.allergies
            self.current_medications = self.patient_id.current_medications
            self.dental_history_summary = self.patient_id.previous_dental_treatments
