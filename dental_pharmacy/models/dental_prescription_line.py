# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DentalPrescriptionLine(models.Model):
    _name = 'dental.prescription.line'
    _description = 'Prescription Line Item'
    _order = 'id asc'

    prescription_id = fields.Many2one(
        'dental.prescription',
        string='Prescription Reference',
        required=True,
        ondelete='cascade',
        index=True
    )
    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        related='prescription_id.patient_id',
        store=True,
        readonly=True
    )
    dentist_id = fields.Many2one(
        'hr.employee',
        string='Dentist',
        related='prescription_id.dentist_id',
        store=True,
        readonly=True
    )
    medicine_id = fields.Many2one(
        'product.product',
        string='Medicine',
        required=True,
        domain=[('is_medicine', '=', True)],
        index=True
    )
    generic_name = fields.Char(
        string='Generic Name',
        related='medicine_id.generic_name',
        readonly=True
    )
    dosage_form = fields.Selection(
        string='Form',
        related='medicine_id.dosage_form',
        readonly=True
    )
    strength = fields.Char(
        string='Strength',
        related='medicine_id.strength',
        readonly=True
    )
    dose = fields.Char(
        string='Dose',
        default='1 tab',
        required=True,
        help='Quantity per administration, e.g., 1 tablet, 500mg, 10ml'
    )
    route = fields.Selection([
        ('oral', 'Oral'),
        ('sublingual', 'Sublingual'),
        ('topical', 'Topical / Mouthwash'),
        ('iv', 'Intravenous (IV)'),
        ('im', 'Intramuscular (IM)'),
        ('inhalation', 'Inhalation'),
        ('other', 'Other'),
    ], string='Route', default='oral', required=True)

    frequency = fields.Selection([
        ('od', 'Once daily (OD)'),
        ('bid', 'Twice daily (BD / BID)'),
        ('tid', 'Three times daily (TDS / TID)'),
        ('qid', 'Four times daily (QDS / QID)'),
        ('q4h', 'Every 4 hours'),
        ('q6h', 'Every 6 hours'),
        ('q8h', 'Every 8 hours'),
        ('prn', 'As needed (PRN)'),
        ('stat', 'Immediately (STAT)'),
    ], string='Frequency', default='bid', required=True)

    duration = fields.Integer(
        string='Duration (Days)',
        default=5,
        required=True,
        help='Treatment course in days'
    )
    quantity = fields.Float(
        string='Prescribed Qty',
        required=True,
        default=1.0,
        help='Total quantity prescribed to the patient'
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='medicine_id.uom_id',
        readonly=True
    )
    instructions = fields.Char(
        string='Instructions',
        default='After meals',
        help='Administration instructions, e.g., After food, Before bed, Rinse 30 secs'
    )
    dispensed_qty = fields.Float(
        string='Dispensed Qty',
        default=0.0,
        readonly=True,
        help='Quantity already dispensed across pharmacy dispensing records.'
    )
    remaining_qty = fields.Float(
        string='Remaining Qty',
        compute='_compute_remaining_qty',
        store=True,
        help='Quantity yet to be dispensed.'
    )
    state = fields.Selection(
        string='Status',
        related='prescription_id.state',
        store=True
    )

    @api.depends('quantity', 'dispensed_qty')
    def _compute_remaining_qty(self):
        for line in self:
            line.remaining_qty = max(0.0, line.quantity - line.dispensed_qty)

    @api.onchange('frequency', 'duration', 'dosage_form')
    def _onchange_frequency_duration(self):
        multiplier_map = {
            'od': 1,
            'bid': 2,
            'tid': 3,
            'qid': 4,
            'q4h': 6,
            'q6h': 4,
            'q8h': 3,
            'prn': 1,
            'stat': 1,
        }
        mult = multiplier_map.get(self.frequency, 1)
        dur = self.duration or 1
        if self.dosage_form in ('tablet', 'capsule'):
            self.quantity = mult * dur
        elif self.dosage_form in ('mouthwash', 'syrup', 'gel'):
            self.quantity = 1.0

    @api.onchange('medicine_id')
    def _onchange_medicine_id(self):
        if self.medicine_id:
            form = self.medicine_id.dosage_form
            if form == 'tablet':
                self.dose = '1 tablet'
                self.route = 'oral'
            elif form == 'capsule':
                self.dose = '1 capsule'
                self.route = 'oral'
            elif form == 'mouthwash':
                self.dose = '15 ml'
                self.route = 'topical'
                self.instructions = 'Rinse mouth for 1 minute twice daily'
            elif form == 'gel':
                self.dose = 'Apply thin layer'
                self.route = 'topical'
                self.instructions = 'Apply to affected area after meals'
            elif form == 'syrup':
                self.dose = '10 ml'
                self.route = 'oral'
