# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_dental_lab_item = fields.Boolean(
        string='Is Dental Lab Item',
        default=False,
        index=True,
        help='Indicates whether this product or material is used or produced by the Dental Laboratory.'
    )
    dental_lab_type = fields.Selection([
        ('raw_material', 'Raw Material'),
        ('teeth', 'Artificial Teeth'),
        ('consumable', 'Dental Consumable'),
        ('crown_bridge', 'Crowns & Bridges'),
        ('denture', 'Dentures'),
        ('veneer', 'Veneers'),
        ('implant', 'Implant Restorations'),
        ('orthodontic', 'Orthodontic Appliances'),
        ('finished_product', 'Finished Dental Products'),
    ], string='Lab Item Category', default='raw_material', index=True)

    dental_material_composition = fields.Selection([
        ('zirconia_ml', 'Zirconia Multilayer 3D Pro'),
        ('zirconia_mono', 'Zirconia Monolithic High Translucency'),
        ('emax_press', 'Lithium Disilicate (IPS E.max Press)'),
        ('emax_cad', 'IPS E.max CAD Block'),
        ('pfm', 'Porcelain Fused to Metal (PFM)'),
        ('cocr_alloy', 'Cobalt-Chromium Alloy (Co-Cr)'),
        ('nicr_alloy', 'Nickel-Chromium Alloy (Ni-Cr)'),
        ('titanium', 'Grade 5 Medical Titanium'),
        ('peek', 'PEEK High Performance Polymer'),
        ('pmma', 'PMMA Temp Block (CAD/CAM)'),
        ('acrylic', 'Heat-Cured Denture Acrylic'),
        ('valplast', 'Flexible Polyamide (Valplast)'),
        ('resin_3d', 'Light-Cure 3D Printing Resin'),
        ('dental_stone', 'Type IV High Strength Die Stone'),
        ('alginate', 'Dental Alginate / Silicone Impression Material'),
        ('other', 'Other Composition'),
    ], string='Material Composition', help='Physical/chemical material structure used for fabrication.')

    dental_shade = fields.Selection([
        ('A1', 'VITA A1'),
        ('A2', 'VITA A2'),
        ('A3', 'VITA A3'),
        ('A3.5', 'VITA A3.5'),
        ('A4', 'VITA A4'),
        ('B1', 'VITA B1'),
        ('B2', 'VITA B2'),
        ('B3', 'VITA B3'),
        ('B4', 'VITA B4'),
        ('C1', 'VITA C1'),
        ('C2', 'VITA C2'),
        ('C3', 'VITA C3'),
        ('C4', 'VITA C4'),
        ('D2', 'VITA D2'),
        ('D3', 'VITA D3'),
        ('D4', 'VITA D4'),
        ('BL1', 'Bleach BL1 (Ultra White)'),
        ('BL2', 'Bleach BL2'),
        ('BL3', 'Bleach BL3'),
        ('BL4', 'Bleach BL4'),
        ('universal', 'Universal / Translucent'),
    ], string='Shade (VITA Classic / Bleach)', help='Color shade matching standard dental shade guides.')

    dental_size = fields.Char(
        string='Size / Disc Thickness',
        help='Size or disc thickness (e.g. 10mm, 14mm, 18mm, 20mm, 25mm, Small, Medium, Large)'
    )
    is_patient_specific = fields.Boolean(
        string='Patient-Specific Custom Item',
        default=False,
        help='True if this is a custom-milled or cast restoration specifically fabricated for a patient prescription.'
    )
    lab_turnaround_days = fields.Integer(
        string='Standard Turnaround (Days)',
        default=3,
        help='Standard laboratory manufacturing turnaround time in business days.'
    )

    lab_order_count = fields.Integer(
        string='Lab Orders Count',
        compute='_compute_lab_order_count'
    )

    def _compute_lab_order_count(self):
        for template in self:
            products = template.product_variant_ids
            template.lab_order_count = self.env['dental.lab.order.line'].search_count([
                ('product_id', 'in', products.ids)
            ]) if products else 0

    def action_view_lab_orders(self):
        self.ensure_one()
        products = self.product_variant_ids
        return {
            'name': _('Lab Orders for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'list,form',
            'domain': [('line_ids.product_id', 'in', products.ids)],
            'context': {'default_is_dental_lab_item': True},
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    lab_order_count = fields.Integer(
        string='Lab Orders Count',
        compute='_compute_lab_order_count'
    )

    def _compute_lab_order_count(self):
        for product in self:
            product.lab_order_count = self.env['dental.lab.order.line'].search_count([
                ('product_id', '=', product.id)
            ])
