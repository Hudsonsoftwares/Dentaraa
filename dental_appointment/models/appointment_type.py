from odoo import models, fields

class DentalAppointmentType(models.Model):
    _name = 'dental.appointment.type'
    _description = 'Dental Appointment Type'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color')
