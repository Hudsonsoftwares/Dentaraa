# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    lab_order_id = fields.Many2one(
        'dental.lab.order',
        string='Dental Lab Order',
        index=True,
        tracking=True,
        help='Dental lab order linked to this manufacturing process.'
    )
    lab_order_line_id = fields.Many2one(
        'dental.lab.order.line',
        string='Dental Lab Order Line',
        index=True,
        help='Tooth restoration line produced in this order.'
    )

    def button_mark_done(self):
        res = super().button_mark_done()
        for prod in self:
            if prod.lab_order_id and prod.state == 'done':
                prod.lab_order_id._on_mrp_production_done(prod)
        return res
