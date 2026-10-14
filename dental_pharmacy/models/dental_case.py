# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DentalCase(models.Model):
    _inherit = 'dental.case'

    prescription_ids = fields.One2many(
        'dental.prescription',
        'case_id',
        string='Prescriptions'
    )
    prescription_count = fields.Integer(
        string='Prescription Count',
        compute='_compute_prescription_count'
    )

    @api.depends('prescription_ids')
    def _compute_prescription_count(self):
        for record in self:
            record.prescription_count = len(record.prescription_ids)

    def action_view_prescriptions(self):
        self.ensure_one()
        return {
            'name': _('Prescriptions for Case %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.prescription',
            'view_mode': 'list,form',
            'domain': [('case_id', '=', self.id)],
            'context': {
                'default_case_id': self.id,
                'default_patient_id': self.patient_id.id,
                'default_dentist_id': self.doctor_id.id if self.doctor_id else False,
            }
        }

    def action_new_prescription(self):
        self.ensure_one()
        return {
            'name': _('New Prescription for %s', self.patient_id.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.prescription',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_case_id': self.id,
                'default_patient_id': self.patient_id.id,
                'default_dentist_id': self.doctor_id.id if self.doctor_id else False,
                'default_appointment_id': self.appointment_id.id if self.appointment_id else False,
            }
        }
