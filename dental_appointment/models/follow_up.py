from odoo import models, fields

class DentalFollowUp(models.Model):
    _name = 'dental.follow.up'
    _description = 'Dental Follow-up'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    appointment_id = fields.Many2one('dental.appointment', string='Original Appointment')
    doctor_id = fields.Many2one('hr.employee', string='Doctor')
    treatment_id = fields.Many2one('product.template', string='Treatment', domain=[('is_dental_treatment', '=', True)])
    
    date = fields.Date(string='Follow-up Date', required=True)
    reason = fields.Text(string='Reason')
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending', tracking=True)
    
    notes = fields.Text(string='Notes')

    def action_done(self):
        for record in self:
            record.state = 'done'
            
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
