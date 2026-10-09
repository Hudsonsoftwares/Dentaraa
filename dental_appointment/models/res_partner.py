from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    appointment_ids = fields.One2many('dental.appointment', 'patient_id', string='Appointments')
    appointment_count = fields.Integer(string='Appointment Count', compute='_compute_appointment_count')
    
    def _compute_appointment_count(self):
        for record in self:
            record.appointment_count = len(record.appointment_ids)

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'name': 'Appointments',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form,calendar',
            'res_model': 'dental.appointment',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }
