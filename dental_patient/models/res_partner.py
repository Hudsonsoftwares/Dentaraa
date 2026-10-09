from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_dental_patient = fields.Boolean(
        string='Is Dental Patient', 
        default=False,
        help="Enable this option to mark this contact as a dental patient and display dental-specific information."
    )
    dental_patient_id = fields.Char(string='Patient ID', readonly=True, copy=False, default='New')
    
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender')
    
    blood_group = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-')
    ], string='Blood Group')
    
    guardian_id = fields.Many2one('res.partner', string='Guardian')
    emergency_contact = fields.Char(string='Emergency Contact')
    
    active_clinic_id = fields.Many2one(
        'res.company', 
        string='Active Clinic/Branch',
        default=lambda self: self.env.company
    )
    
    # Medical History
    medical_history = fields.Html(string='Medical History')
    allergies = fields.Html(string='Allergies')
    existing_conditions = fields.Html(string='Existing Conditions')
    current_medications = fields.Html(string='Current Medications')
    previous_surgeries = fields.Html(string='Previous Surgeries')
    
    # Dental History
    dental_history = fields.Html(string='Dental History')
    previous_dental_treatments = fields.Html(string='Previous Dental Treatments')
    last_dental_visit = fields.Date(string='Last Dental Visit')
    oral_hygiene = fields.Selection([
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string='Oral Hygiene')
    smoking_tobacco_history = fields.Selection([
        ('none', 'None'),
        ('occasional', 'Occasional'),
        ('frequent', 'Frequent')
    ], string='Smoking/Tobacco History')
    brushing_frequency = fields.Selection([
        ('rarely', 'Rarely'),
        ('once', 'Once daily'),
        ('twice', 'Twice daily')
    ], string='Brushing Frequency')
    
    clinical_alerts = fields.Html(string='Clinical Alerts')

    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                record.age = relativedelta(date.today(), record.date_of_birth).years
            else:
                record.age = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            is_patient = vals.get('is_dental_patient', self.env.context.get('default_is_dental_patient', False))
            if is_patient and vals.get('dental_patient_id', _('New')) == _('New'):
                vals['dental_patient_id'] = self.env['ir.sequence'].next_by_code('dental.patient') or _('New')
        return super(ResPartner, self).create(vals_list)

    @api.onchange('name', 'date_of_birth', 'phone')
    def _onchange_check_duplicate_patient(self):
        if not self.is_dental_patient:
            return
            
        domain = [('is_dental_patient', '=', True)]
        origin_id = self._origin.id if self._origin else False
        if origin_id:
            domain.append(('id', '!=', origin_id))
            
        if self.phone:
            duplicate = self.env['res.partner'].search(domain + [('phone', '=', self.phone)], limit=1)
            if duplicate:
                return {
                    'warning': {
                        'title': _('Duplicate Patient Warning'),
                        'message': _('A patient with phone number %s already exists: %s') % (self.phone, duplicate.name)
                    }
                }
                
        if self.name and self.date_of_birth:
            duplicate = self.env['res.partner'].search(domain + [
                ('name', '=ilike', self.name),
                ('date_of_birth', '=', self.date_of_birth)
            ], limit=1)
            if duplicate:
                return {
                    'warning': {
                        'title': _('Duplicate Patient Warning'),
                        'message': _('A patient with the same name and Date of Birth already exists: %s') % duplicate.name
                    }
                }
