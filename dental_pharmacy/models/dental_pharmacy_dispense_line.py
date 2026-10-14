# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DentalPharmacyDispenseLine(models.Model):
    _name = 'dental.pharmacy.dispense.line'
    _description = 'Pharmacy Dispense Order Line'
    _order = 'id asc'

    dispense_id = fields.Many2one(
        'dental.pharmacy.dispense',
        string='Dispense Reference',
        required=True,
        ondelete='cascade',
        index=True
    )
    prescription_line_id = fields.Many2one(
        'dental.prescription.line',
        string='Prescribed Item',
        required=True,
        index=True
    )
    medicine_id = fields.Many2one(
        'product.product',
        string='Medicine',
        related='prescription_line_id.medicine_id',
        store=True,
        readonly=True
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
    prescribed_qty = fields.Float(
        string='Prescribed Qty',
        related='prescription_line_id.quantity',
        readonly=True
    )
    previously_dispensed_qty = fields.Float(
        string='Prior Dispensed',
        related='prescription_line_id.dispensed_qty',
        readonly=True
    )
    remaining_qty = fields.Float(
        string='Remaining Qty',
        related='prescription_line_id.remaining_qty',
        readonly=True
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Batch / Lot',
        domain="[('product_id', '=', medicine_id), ('is_expired', '=', False)]",
        help='Select physical stock batch to dispense from. Expired batches are excluded.'
    )
    lot_expiry_date = fields.Date(
        string='Batch Expiry',
        related='lot_id.expiry_date',
        readonly=True
    )
    lot_stock_qty = fields.Float(
        string='Batch Stock Qty',
        compute='_compute_lot_stock_qty',
        help='Available stock on hand in this batch within the selected dispensing location.'
    )
    qty_to_dispense = fields.Float(
        string='Qty to Dispense',
        required=True,
        default=1.0,
        help='Quantity of medicine to be physically dispensed in this order.'
    )
    unit_price = fields.Float(
        string='Unit Price',
        default=0.0,
        help='Selling price per unit'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='dispense_id.currency_id',
        readonly=True
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True
    )
    state = fields.Selection(
        string='Status',
        related='dispense_id.state',
        store=True
    )

    @api.depends('lot_id', 'dispense_id.location_id')
    def _compute_lot_stock_qty(self):
        for line in self:
            if line.lot_id and line.dispense_id.location_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.medicine_id.id),
                    ('lot_id', '=', line.lot_id.id),
                    ('location_id', '=', line.dispense_id.location_id.id)
                ])
                line.lot_stock_qty = sum(quants.mapped('quantity'))
            else:
                line.lot_stock_qty = 0.0

    @api.depends('qty_to_dispense', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = (line.qty_to_dispense or 0.0) * (line.unit_price or 0.0)

    @api.onchange('prescription_line_id')
    def _onchange_prescription_line_id(self):
        if self.prescription_line_id:
            self.medicine_id = self.prescription_line_id.medicine_id
            self.qty_to_dispense = self.prescription_line_id.remaining_qty
            self.unit_price = self.prescription_line_id.medicine_id.list_price
