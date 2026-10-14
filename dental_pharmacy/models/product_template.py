# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_medicine = fields.Boolean(
        string='Is Medicine',
        default=False,
        index=True,
        help='Indicates whether this product is a pharmaceutical item managed by the dental pharmacy.'
    )
    generic_name = fields.Char(
        string='Generic / Chemical Name',
        tracking=True,
        index=True,
        help='Active pharmaceutical ingredient (API), e.g., Amoxicillin, Ibuprofen, Chlorhexidine Gluconate'
    )
    medicine_category_id = fields.Many2one(
        'dental.medicine.category',
        string='Medicine Category',
        tracking=True,
        index=True
    )
    dosage_form = fields.Selection([
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup / Oral Suspension'),
        ('injection', 'Injection / Cartridge'),
        ('mouthwash', 'Mouthwash / Oral Rinse'),
        ('gel', 'Oral Gel / Ointment'),
        ('paste', 'Dental Paste'),
        ('drops', 'Drops'),
        ('spray', 'Spray'),
        ('other', 'Other'),
    ], string='Dosage Form', default='tablet', tracking=True)

    strength = fields.Char(
        string='Strength / Potency',
        tracking=True,
        help='e.g., 500 mg, 625 mg, 400 mg, 0.2% w/v, 2% with 1:80,000 Epinephrine'
    )
    manufacturer_name = fields.Char(
        string='Manufacturer',
        help='Pharmaceutical manufacturer or pharmaceutical brand'
    )
    manufacturer_id = fields.Many2one(
        'res.partner',
        string='Supplier / Vendor',
        domain="['|', ('is_company', '=', True), ('supplier_rank', '>', 0)]",
        help='Primary supplier / pharmaceutical distributor for replenishment'
    )
    dosage_unit = fields.Char(
        string='Dosage Unit',
        default='Tablets',
        help='Unit representation for clinical prescribing, e.g., Tablets, Capsules, ml, Vials'
    )
    prescription_required = fields.Boolean(
        string='Prescription Required (Rx)',
        default=True,
        tracking=True,
        help='If checked, this medicine strictly requires a doctor prescription before dispensing.'
    )
    reorder_level = fields.Float(
        string='Reorder Level (Min Stock)',
        default=10.0,
        tracking=True,
        help='Threshold below which low stock alert is triggered on the pharmacy dashboard.'
    )
    stock_status = fields.Selection([
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock')
    ], string='Stock Status', compute='_compute_stock_status')

    lot_count = fields.Integer(string='Batch Count', compute='_compute_lot_count')

    @api.depends('qty_available', 'reorder_level')
    def _compute_stock_status(self):
        for template in self:
            if not template.is_medicine:
                template.stock_status = False
            elif template.qty_available <= 0:
                template.stock_status = 'out_of_stock'
            elif template.qty_available <= template.reorder_level:
                template.stock_status = 'low_stock'
            else:
                template.stock_status = 'in_stock'

    def _compute_lot_count(self):
        for template in self:
            product_ids = template.product_variant_ids.ids
            if product_ids:
                template.lot_count = self.env['stock.lot'].search_count([('product_id', 'in', product_ids)])
            else:
                template.lot_count = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_medicine'):
                if 'is_storable' in self._fields and 'is_storable' not in vals:
                    vals['is_storable'] = True
                if 'tracking' not in vals:
                    vals['tracking'] = 'lot'
        return super().create(vals_list)

    @api.onchange('is_medicine')
    def _onchange_is_medicine(self):
        if self.is_medicine:
            # Medicines should track stock and use lots/batches
            if not self.type:
                self.type = 'consu' # In Odoo 20 stockable is consu with is_storable=True or tracking
            if hasattr(self, 'is_storable'):
                self.is_storable = True
            self.tracking = 'lot'

    def action_view_batches(self):
        self.ensure_one()
        product_ids = self.product_variant_ids.ids
        return {
            'name': _('Batches for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('product_id', 'in', product_ids)],
            'context': {'default_product_id': product_ids[0] if len(product_ids) == 1 else False},
        }
