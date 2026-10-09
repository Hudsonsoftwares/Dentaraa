from odoo import models, fields

class DentalRecallRule(models.Model):
    _name = 'dental.recall.rule'
    _description = 'Dental Recall Rule'

    name = fields.Char(string='Name', required=True)
    treatment_id = fields.Many2one('product.template', string='Treatment', domain=[('is_dental_treatment', '=', True)])
    interval_number = fields.Integer(string='Interval', required=True, default=6)
    interval_type = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ], string='Interval Type', required=True, default='months')

class DentalRecall(models.Model):
    _name = 'dental.recall'
    _description = 'Dental Recall'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)])
    treatment_id = fields.Many2one('product.template', string='Treatment', domain=[('is_dental_treatment', '=', True)])
    last_appointment_id = fields.Many2one('dental.appointment', string='Last Appointment')
    due_date = fields.Date(string='Due Date', required=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('called', 'Called'),
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending', tracking=True)
    notes = fields.Text(string='Notes')

    def action_called(self):
        for record in self:
            record.state = 'called'

    def action_booked(self):
        for record in self:
            record.state = 'booked'
            
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
