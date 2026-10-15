from odoo import models, fields

class DentalAppointmentType(models.Model):
    _name = 'dental.appointment.type'
    _description = 'Dental Appointment Type'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color')
    duration = fields.Float(string='Duration (Minutes)', default=30.0)
    description = fields.Text(string='Description')
    price = fields.Float(string='Estimated Price', default=0.0)
    icon = fields.Char(string='Icon Class', default='fa-stethoscope')
    active = fields.Boolean(string='Active', default=True)
