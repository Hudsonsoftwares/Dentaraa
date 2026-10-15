# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class QualityAlert(models.Model):
    _inherit = 'quality.alert'

    lab_order_id = fields.Many2one(
        'dental.lab.order',
        string='Dental Lab Order',
        index=True,
        tracking=True,
        help='Patient lab order that originated this defect/alert.'
    )
    lab_order_line_id = fields.Many2one(
        'dental.lab.order.line',
        string='Lab Order Line',
        index=True,
        help='Specific tooth/restoration line affected by the defect.'
    )
