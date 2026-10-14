# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta

class StockLot(models.Model):
    _inherit = 'stock.lot'

    is_medicine = fields.Boolean(
        related='product_id.is_medicine',
        string='Is Medicine Batch',
        store=True,
        index=True
    )
    expiry_date = fields.Date(
        string='Expiry Date',
        index=True,
        tracking=True,
        help='Date after which this pharmaceutical batch becomes unusable and cannot be dispensed.'
    )
    manufacturing_date = fields.Date(
        string='Manufacturing Date',
        tracking=True,
        help='Date of manufacture for this batch'
    )
    alert_date = fields.Date(
        string='Alert Date',
        compute='_compute_alert_date',
        store=True,
        readonly=False,
        help='Date when near-expiry warnings should be triggered (defaults to 60 days before expiry date).'
    )
    days_to_expiry = fields.Integer(
        string='Days to Expiry',
        compute='_compute_expiry_status',
        store=True,
        help='Remaining days before this batch reaches its expiration date.'
    )
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_expiry_status',
        store=True,
        index=True,
        help='True if the current date is strictly after the batch expiry date.'
    )
    expiry_status = fields.Selection([
        ('valid', 'Valid / Safe'),
        ('near_expiry', 'Near Expiry (≤ 60 Days)'),
        ('expired', 'Expired (Do Not Dispense)')
    ], string='Batch Status', compute='_compute_expiry_status', store=True, index=True)

    available_qty = fields.Float(
        string='On Hand Qty',
        compute='_compute_lot_quantities',
        help='Physical stock on hand for this specific batch in internal locations.'
    )

    @api.depends('expiry_date')
    def _compute_alert_date(self):
        for lot in self:
            if lot.expiry_date and not lot.alert_date:
                lot.alert_date = lot.expiry_date - timedelta(days=60)
            elif not lot.expiry_date:
                lot.alert_date = False

    @api.depends('expiry_date')
    def _compute_expiry_status(self):
        today = fields.Date.context_today(self)
        for lot in self:
            if not lot.expiry_date:
                lot.days_to_expiry = 9999
                lot.is_expired = False
                lot.expiry_status = 'valid'
                continue

            delta = (lot.expiry_date - today).days
            lot.days_to_expiry = delta
            if delta < 0:
                lot.is_expired = True
                lot.expiry_status = 'expired'
            elif delta <= 60:
                lot.is_expired = False
                lot.expiry_status = 'near_expiry'
            else:
                lot.is_expired = False
                lot.expiry_status = 'valid'

    def _compute_lot_quantities(self):
        for lot in self:
            quants = self.env['stock.quant'].search([
                ('lot_id', '=', lot.id),
                ('location_id.usage', '=', 'internal')
            ])
            lot.available_qty = sum(quants.mapped('quantity'))

    @api.depends('name', 'expiry_date', 'expiry_status')
    def _compute_display_name(self):
        for lot in self:
            if lot.is_medicine and lot.expiry_date:
                status_label = ""
                if lot.expiry_status == 'expired':
                    status_label = " [EXPIRED]"
                elif lot.expiry_status == 'near_expiry':
                    status_label = " [NEAR EXPIRY]"
                lot.display_name = f"{lot.name} (Exp: {lot.expiry_date}){status_label}"
            else:
                super(StockLot, lot)._compute_display_name()
