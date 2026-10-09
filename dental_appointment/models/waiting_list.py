from odoo import models, fields

class DentalWaitingList(models.Model):
    _name = 'dental.waiting.list'
    _description = 'Dental Waiting List'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    doctor_id = fields.Many2one('hr.employee', string='Preferred Doctor', tracking=True)
    date_from = fields.Datetime(string='Preferred Time From')
    date_to = fields.Datetime(string='Preferred Time To')
    treatment_id = fields.Many2one('product.template', string='Treatment', domain=[('is_dental_treatment', '=', True)])
    
    priority = fields.Selection([
        ('normal', 'Normal'),
        ('high', 'High'),
        ('emergency', 'Emergency')
    ], string='Priority', default='normal', tracking=True)
    
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('assigned', 'Assigned'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='waiting', tracking=True)
    
    notes = fields.Text(string='Notes')

    def action_assign(self):
        for record in self:
            record.state = 'assigned'
            
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
