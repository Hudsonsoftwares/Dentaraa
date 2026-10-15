# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DentalLabDashboard(models.Model):
    _name = 'dental.lab.dashboard'
    _description = 'Dental Laboratory Real-Time KPI Dashboard'

    name = fields.Char(string='Name', default='Dental Laboratory Overview')

    total_open_orders = fields.Integer(string='Open Lab Orders', compute='_compute_dashboard_kpis')
    awaiting_submission = fields.Integer(string='Draft Orders', compute='_compute_dashboard_kpis')
    in_production_count = fields.Integer(string='In Production', compute='_compute_dashboard_kpis')
    qc_pending_count = fields.Integer(string='Awaiting QC Inspection', compute='_compute_dashboard_kpis')
    rework_count = fields.Integer(string='Quality Failures / Rework', compute='_compute_dashboard_kpis')
    finished_awaiting_dispatch = fields.Integer(string='Finished Awaiting Dispatch', compute='_compute_dashboard_kpis')
    dispatched_in_transit = fields.Integer(string='Dispatched In Transit', compute='_compute_dashboard_kpis')
    awaiting_dentist_acceptance = fields.Integer(string='Awaiting Clinical Acceptance', compute='_compute_dashboard_kpis')
    external_lab_pending = fields.Integer(string='External Lab In Progress', compute='_compute_dashboard_kpis')
    overdue_orders_count = fields.Integer(string='Overdue Orders', compute='_compute_dashboard_kpis')
    low_stock_materials_count = fields.Integer(string='Low Stock Materials', compute='_compute_dashboard_kpis')
    active_mrp_count = fields.Integer(string='Active MRP Orders', compute='_compute_dashboard_kpis')

    def _compute_dashboard_kpis(self):
        Order = self.env['dental.lab.order']
        today = fields.Date.context_today(self)
        for rec in self:
            rec.total_open_orders = Order.search_count([('state', 'not in', ('closed', 'cancelled'))])
            rec.awaiting_submission = Order.search_count([('state', '=', 'draft')])
            rec.in_production_count = Order.search_count([('state', '=', 'in_production')])
            rec.qc_pending_count = Order.search_count([('state', '=', 'qc_pending')])
            rec.rework_count = Order.search_count([('state', '=', 'rework')])
            rec.finished_awaiting_dispatch = Order.search_count([('state', 'in', ('qc_approved', 'finished'))])
            rec.dispatched_in_transit = Order.search_count([('state', '=', 'dispatched')])
            rec.awaiting_dentist_acceptance = Order.search_count([('state', '=', 'received_clinic')])
            rec.external_lab_pending = Order.search_count([('lab_type', '=', 'external'), ('state', 'not in', ('closed', 'cancelled', 'draft'))])
            rec.overdue_orders_count = Order.search_count([('due_date', '<', today), ('state', 'not in', ('closed', 'cancelled'))])
            
            # Low stock lab materials: products with is_dental_lab_item where qty_available <= 2
            rec.low_stock_materials_count = self.env['product.product'].search_count([
                ('is_dental_lab_item', '=', True),
                ('qty_available', '<=', 2.0)
            ])
            rec.active_mrp_count = self.env['mrp.production'].search_count([
                ('state', 'in', ('confirmed', 'progress', 'to_close')),
                ('lab_order_id', '!=', False)
            ])

    # Drill-down action methods
    def action_view_open_orders(self):
        return {
            'name': _('Open Dental Lab Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'list,form',
            'domain': [('state', 'not in', ('closed', 'cancelled'))],
        }

    def action_view_qc_pending(self):
        return {
            'name': _('Orders Awaiting Quality Inspection'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'qc_pending')],
        }

    def action_view_rework(self):
        return {
            'name': _('Orders Requiring Rework / Defect Correction'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'rework')],
        }

    def action_view_in_production(self):
        return {
            'name': _('Active In-Production Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'in_production')],
        }

    def action_view_external_pending(self):
        return {
            'name': _('Orders with External Laboratories'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'list,form',
            'domain': [('lab_type', '=', 'external'), ('state', 'not in', ('closed', 'cancelled'))],
        }

    def action_view_overdue(self):
        today = fields.Date.context_today(self)
        return {
            'name': _('Overdue Dental Lab Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'list,form',
            'domain': [('due_date', '<', today), ('state', 'not in', ('closed', 'cancelled'))],
        }

    def action_view_low_stock(self):
        return {
            'name': _('Low Stock Dental Lab Materials'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'domain': [('is_dental_lab_item', '=', True), ('qty_available', '<=', 2.0)],
        }
