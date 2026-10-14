# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    dental_case_id = fields.Many2one(
        'dental.case',
        string='Dental Case',
        index=True,
        help='Linked dental consultation case'
    )
    dental_prescription_id = fields.Many2one(
        'dental.prescription',
        string='Prescription Reference',
        index=True,
        help='Dental clinical prescription associated with this invoice'
    )
    pharmacy_dispense_id = fields.Many2one(
        'dental.pharmacy.dispense',
        string='Pharmacy Dispense Order',
        index=True,
        help='Originating pharmacy dispensing order'
    )
    is_pharmacy_invoice = fields.Boolean(
        string='Pharmacy Invoice',
        compute='_compute_is_pharmacy_invoice',
        store=True,
        index=True
    )

    @api.depends('pharmacy_dispense_id', 'dental_prescription_id')
    def _compute_is_pharmacy_invoice(self):
        for move in self:
            move.is_pharmacy_invoice = bool(move.pharmacy_dispense_id or move.dental_prescription_id)

    def action_view_pharmacy_dispense(self):
        self.ensure_one()
        if not self.pharmacy_dispense_id:
            return False
        return {
            'name': _('Pharmacy Dispense Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.pharmacy.dispense',
            'view_mode': 'form',
            'res_id': self.pharmacy_dispense_id.id,
            'target': 'current',
        }
