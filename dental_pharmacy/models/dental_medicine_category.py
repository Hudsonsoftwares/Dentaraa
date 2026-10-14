# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DentalMedicineCategory(models.Model):
    _name = 'dental.medicine.category'
    _description = 'Dental Medicine Category'
    _order = 'name asc'

    name = fields.Char(string='Category Name', required=True, translate=True)
    code = fields.Char(string='Code', help='Short therapeutic code or classification, e.g., ATB, ANL, LA')
    description = fields.Text(string='Description / Clinical Notes')
    active = fields.Boolean(string='Active', default=True)
    medicine_ids = fields.One2many('product.template', 'medicine_category_id', string='Medicines')
    medicine_count = fields.Integer(string='Medicine Count', compute='_compute_medicine_count')

    @api.depends('medicine_ids')
    def _compute_medicine_count(self):
        for record in self:
            record.medicine_count = len(record.medicine_ids)

    def action_view_medicines(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,kanban,form',
            'domain': [('medicine_category_id', '=', self.id)],
            'context': {'default_medicine_category_id': self.id, 'default_is_medicine': True},
        }
