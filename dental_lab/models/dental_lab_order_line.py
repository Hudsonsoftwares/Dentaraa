# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DentalLabOrderLine(models.Model):
    _name = 'dental.lab.order.line'
    _description = 'Tooth-Specific Dental Lab Order Line'
    _order = 'tooth_number asc, id asc'

    order_id = fields.Many2one(
        'dental.lab.order',
        string='Lab Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        related='order_id.company_id',
        store=True,
        index=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='order_id.currency_id',
        store=True
    )

    tooth_number = fields.Char(
        string='FDI Tooth / Range',
        required=True,
        help='FDI tooth notation (e.g., 11, 21, 14-16 for bridge, 36, 47, Maxillary Arch, Mandibular Arch)'
    )
    restoration_type = fields.Selection([
        ('crown', 'Full Crown'),
        ('bridge', 'Multi-Unit Bridge'),
        ('inlay_onlay', 'Inlay / Onlay'),
        ('veneer', 'Veneer / Laminate'),
        ('denture_complete', 'Complete Denture (Full Arch)'),
        ('denture_partial', 'Cast Partial / Acrylic Denture'),
        ('implant_abutment', 'Custom Titanium / Zirconia Abutment'),
        ('implant_crown', 'Screw-Retained Implant Crown'),
        ('ortho_appliance', 'Orthodontic Appliance / Expander'),
        ('nightguard', 'Nightguard / Bruxism Splint'),
        ('retainer', 'Clear Retainer (Essix / Hawley)'),
        ('surgical_guide', '3D Printed Surgical Guide'),
        ('custom_tray', 'Custom Impression Tray'),
        ('other', 'Other Dental Appliance'),
    ], string='Restoration / Appliance Type', required=True, default='crown')

    product_id = fields.Many2one(
        'product.product',
        string='Catalog Product / Material',
        domain="[('is_dental_lab_item', '=', True)]",
        help='Standard lab product or billable item linked to this restoration line.'
    )
    material = fields.Selection([
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
        ('other', 'Other Custom Material'),
    ], string='Specific Material', default='zirconia_ml')

    shade = fields.Selection([
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
        ('BL1', 'Bleach BL1'),
        ('BL2', 'Bleach BL2'),
        ('BL3', 'Bleach BL3'),
        ('BL4', 'Bleach BL4'),
        ('universal', 'Universal / Multi-Shade'),
    ], string='Shade', default='A2')

    stump_shade = fields.Char(string='Stump Die Shade')
    quantity = fields.Float(string='Units / Qty', default=1.0, required=True)
    unit_price = fields.Monetary(string='Unit Price')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)

    technical_notes = fields.Text(string='Tooth Specifications / Characterization')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_production', 'In Production'),
        ('qc_pending', 'QC Pending'),
        ('qc_passed', 'QC Passed'),
        ('qc_failed', 'QC Failed'),
        ('rework', 'Rework Required'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Line Status', default='draft')

    rework_count = fields.Integer(string='Rework Count', default=0)
    rework_notes = fields.Text(string='Rework / Defect History')
    quality_check_id = fields.Many2one('quality.check', string='Latest Quality Inspection', readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.list_price
            if self.product_id.dental_shade:
                self.shade = self.product_id.dental_shade
            if self.product_id.dental_material_composition:
                self.material = self.product_id.dental_material_composition
