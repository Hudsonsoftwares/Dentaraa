from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dental_role = fields.Selection([
        ('dentist', 'Dentist'),
        ('assistant', 'Dental Assistant'),
        ('receptionist', 'Receptionist'),
        ('lab_tech', 'Lab Technician'),
        ('pharmacist', 'Pharmacist'),
        ('manager', 'Clinic Manager'),
        ('admin', 'Dental Administrator'),
    ], string='Dental Role', tracking=True, help='Assigned role within the Dental Clinic system')


    registration_number = fields.Char(
        string='Dental License / Reg No.',
        tracking=True,
        help='Dental Council / State Board registration number for practicing dentists',
    )
    specialization = fields.Char(
        string='Specialization',
        help='e.g., Orthodontics, Endodontics, Periodontics, Prosthodontics, Pedodontics, Oral Surgery, General Dentistry',
    )
    consultation_fee = fields.Monetary(
        string='Standard Consultation Fee',
        currency_field='currency_id',
        help='Default consultation charge for this doctor',
    )
    signature_image = fields.Binary(
        string='Doctor Signature Image',
        attachment=True,
        help='Scanned signature image used for digital prescriptions and treatment consents',
    )
    digital_stamp = fields.Binary(
        string='Digital Clinic Stamp',
        attachment=True,
        help='Digital official stamp used for certifications and official reports',
    )
    is_dentist = fields.Boolean(
        string='Is Dentist',
        compute='_compute_is_dentist',
        store=True,
        help='Technical flag to filter doctors and dentists across clinical appointments and treatments',
    )

    @api.depends('dental_role')
    def _compute_is_dentist(self):
        for employee in self:
            employee.is_dentist = (employee.dental_role == 'dentist')

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    is_dentist = fields.Boolean(readonly=True)
