from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_dental_treatment = fields.Boolean(string='Is Dental Treatment', default=False)
    treatment_code = fields.Char(string='Treatment Code')
    dental_treatment_category_id = fields.Many2one('dental.treatment.category', string='Dental Treatment Category')
    treatment_duration = fields.Float(string='Treatment Duration', help='Duration in hours or format (e.g. 1.5 for 1h 30m)')
    number_of_visits = fields.Integer(string='Number of Visits', default=1)
    followup_interval = fields.Char(string='Follow-up Interval', help='e.g., 6 Months, 1 Year')
    is_lab_required = fields.Boolean(string='Lab Required', default=False)
    is_consent_required = fields.Boolean(string='Consent Required', default=False)
    material_ids = fields.Many2many(
        'product.product',
        'product_template_dental_materials_rel',
        'template_id', 'product_id',
        string='Materials / Consumables',
        domain="[('type', 'in', ['consu', 'product'])]"
    )
