from odoo import models, fields

class DentalTreatmentCategory(models.Model):
    _name = 'dental.treatment.category'
    _description = 'Dental Treatment Category'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
