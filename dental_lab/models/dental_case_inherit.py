# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DentalCase(models.Model):
    _inherit = 'dental.case'

    lab_order_ids = fields.One2many(
        'dental.lab.order',
        'case_id',
        string='Dental Lab Orders'
    )
    lab_order_count = fields.Integer(
        string='Lab Orders Count',
        compute='_compute_lab_order_count'
    )

    @api.depends('lab_order_ids')
    def _compute_lab_order_count(self):
        for record in self:
            record.lab_order_count = len(record.lab_order_ids)

    def action_view_lab_orders(self):
        self.ensure_one()
        return {
            'name': _('Lab Orders for Case %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'list,form',
            'domain': [('case_id', '=', self.id)],
            'context': {
                'default_case_id': self.id,
                'default_patient_id': self.patient_id.id,
                'default_dentist_id': self.doctor_id.id if self.doctor_id else False,
            }
        }

    def action_new_lab_order(self):
        self.ensure_one()
        # Open the creation wizard to prevent duplicate submissions and allow selecting tooth lines
        return {
            'name': _('Create Dental Lab Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_case_id': self.id,
                'default_patient_id': self.patient_id.id,
                'default_dentist_id': self.doctor_id.id if self.doctor_id else False,
                'default_appointment_id': self.appointment_id.id if self.appointment_id else False,
            }
        }
