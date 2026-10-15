# -*- coding: utf-8 -*-

# pyrefly: ignore [missing-import]
from odoo import api, fields, models


class QualityCheckFail(models.TransientModel):
    _name = 'quality.check.fail'
    _description = 'Quality Check Fail Wizard'

    check_id = fields.Many2one('quality.check', string='Quality Check', required=True, ondelete='cascade')
    failure_location_id = fields.Many2one('stock.location', string='Failure Location', domain="[('usage', '=', 'internal')]")
    message = fields.Char(string='Message', compute='_compute_message')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'check_id' in res and 'failure_location_id' in fields_list:
            check = self.env['quality.check'].browse(res['check_id'])
            if check.point_id and check.point_id.failure_location_ids:
                res['failure_location_id'] = check.point_id.failure_location_ids[0].id
        return res

    @api.depends('check_id.measure', 'check_id.tolerance_min', 'check_id.tolerance_max', 'check_id.norm_unit')
    def _compute_message(self):
        for wizard in self:
            if wizard.check_id:
                measure = wizard.check_id.measure
                t_min = wizard.check_id.tolerance_min
                t_max = wizard.check_id.tolerance_max
                unit = wizard.check_id.norm_unit or ''
                wizard.message = f"You measured {measure:.2f} {unit} and it should be between {t_min:.2f} and {t_max:.2f} {unit}."
            else:
                wizard.message = ""

    def action_confirm(self):
        self.ensure_one()
        self.check_id.do_fail(self.failure_location_id.id if self.failure_location_id else None)
        return {'type': 'ir.actions.act_window_close'}
