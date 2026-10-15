# -*- coding: utf-8 -*-
from odoo import _, api, fields, models  # pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    quality_check_ids = fields.One2many('quality.check', 'picking_id', string='Quality Checks')
    quality_check_count = fields.Integer(compute='_compute_quality_check_count')
    quality_check_fail_count = fields.Integer(compute='_compute_quality_check_count')
    quality_check_todo = fields.Boolean(compute='_compute_quality_check_todo')
    quality_alert_ids = fields.One2many(
        'quality.alert', 'picking_id', string='Quality Alerts')
    quality_alert_count = fields.Integer(compute='_compute_quality_alert_count')

    @api.depends('quality_check_ids.quality_state')
    def _compute_quality_check_count(self):
        for picking in self:
            picking.quality_check_count = len(picking.quality_check_ids)
            picking.quality_check_fail_count = len(
                picking.quality_check_ids.filtered(lambda c: c.quality_state == 'fail'))

    @api.depends('quality_check_ids.quality_state')
    def _compute_quality_check_todo(self):
        for picking in self:
            picking.quality_check_todo = any(c.quality_state == 'none' for c in picking.quality_check_ids)

    @api.depends('quality_alert_ids')
    def _compute_quality_alert_count(self):
        for picking in self:
            picking.quality_alert_count = len(picking.quality_alert_ids)


    def _generate_quality_checks(self):
        self.ensure_one()
        products = self.move_ids.product_id
        if not products:
            return self.env['quality.check']
        points = self.env['quality.point']._get_matching_points(
            company=self.company_id,
            products=products,
            picking_type=self.picking_type_id,
        )
        common_vals = {
            'picking_id': self.id,
            'company_id': self.company_id.id,
        }
        return self.env['quality.check']._create_checks_from_points(
            points, common_vals, products=products)

    def _pre_action_done_hook(self):
        for picking in self:
            pending = picking.quality_check_ids.filtered(lambda c: c.quality_state == 'none')
            if pending:
                return picking.action_open_quality_check_wizard()
        return super()._pre_action_done_hook()

    def action_open_quality_check_wizard(self):
        self.ensure_one()
        return {
            'name': _('Quality Check'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_picking_id': self.id, 'active_model': 'stock.picking', 'active_id': self.id},
        }

    def action_view_quality_checks(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'Quality.action_quality_check')
        action['domain'] = [('picking_id', '=', self.id)]
        action['context'] = {
            'default_picking_id': self.id,
            'default_company_id': self.company_id.id,
        }
        return action

    def action_view_quality_alerts(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'Quality.action_quality_alert')
        action['domain'] = [('picking_id', '=', self.id)]
        action['context'] = {'default_picking_id': self.id}
        return action

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_confirm(self, merge=True, merge_into=False, **kwargs):
        res = super()._action_confirm(merge=merge, merge_into=merge_into, **kwargs)
        pickings = res.mapped('picking_id') if hasattr(res, 'mapped') else self.mapped('picking_id')
        for picking in pickings:
            picking._generate_quality_checks()
        return res
