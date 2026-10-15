# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta

class DentalLabReworkWizard(models.TransientModel):
    _name = 'dental.lab.rework.wizard'
    _description = 'Dental Laboratory Rework & Defect Correction Wizard'

    order_id = fields.Many2one('dental.lab.order', string='Lab Order', required=True)
    order_line_id = fields.Many2one('dental.lab.order.line', string='Restoration Line')
    check_id = fields.Many2one('quality.check', string='Failed Quality Inspection')

    rework_type = fields.Selection([
        ('adjustment', 'Minor Lab Adjustment & Repolish'),
        ('shade_correction', 'Shade Modification / Re-Glaze / Characterization'),
        ('margin_fit', 'Marginal Fit & Seating Correction'),
        ('remake', 'Complete Remake (New Milling / Casting)'),
        ('external_return', 'Return to External Commercial Lab for Correction'),
    ], string='Rework Classification', default='shade_correction', required=True)

    rework_reason = fields.Text(
        string='Defect Description & Correction Instructions',
        required=True,
        help='Detailed technical explanation of what failed and specific steps required for correction.'
    )
    technician_id = fields.Many2one(
        'res.users',
        string='Assigned Rework Technician',
        help='Technician allocated to perform the corrective action.'
    )
    new_due_date = fields.Date(
        string='Revised Due Date',
        required=True,
        default=lambda self: fields.Date.context_today(self) + timedelta(days=2)
    )

    def action_confirm_rework(self):
        self.ensure_one()
        order = self.order_id
        order.write({
            'state': 'rework',
            'due_date': self.new_due_date,
            'technician_id': self.technician_id.id if self.technician_id else order.technician_id.id,
        })

        target_lines = self.order_line_id if self.order_line_id else order.line_ids
        for line in target_lines:
            line.write({
                'state': 'rework',
                'rework_count': line.rework_count + 1,
                'rework_notes': (line.rework_notes or '') + _("\n[%s] Rework requested: %s - Reason: %s") % (
                    fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
                    dict(self._fields['rework_type'].selection).get(self.rework_type),
                    self.rework_reason
                ),
            })

        # If originating from an existing quality check, create a linked re-inspection check
        if self.check_id:
            new_check = self.env['quality.check'].create({
                'title': _("Re-inspection: %s") % (self.check_id.title or self.check_id.name),
                'point_id': self.check_id.point_id.id if self.check_id.point_id else False,
                'lab_order_id': order.id,
                'lab_order_line_id': self.order_line_id.id if self.order_line_id else self.check_id.lab_order_line_id.id,
                'product_id': self.check_id.product_id.id if self.check_id.product_id else False,
                'team_id': self.check_id.team_id.id if self.check_id.team_id else False,
                'user_id': self.technician_id.id if self.technician_id else self.check_id.user_id.id,
                'test_type': self.check_id.test_type,
                'dental_inspection_stage': self.check_id.dental_inspection_stage,
                'instructions': self.check_id.instructions,
                'quality_state': 'none',
                'is_rework': True,
                'parent_check_id': self.check_id.id,
                'rework_reason': self.rework_reason,
            })
            self.check_id.write({'rework_reason': self.rework_reason})

        order.message_post(
            body=_("<b>Rework Initiated:</b> %s.<br/><b>Instructions:</b> %s<br/><b>Revised Delivery:</b> %s") % (
                dict(self._fields['rework_type'].selection).get(self.rework_type),
                self.rework_reason,
                self.new_due_date
            ),
            message_type='comment'
        )

        return {'type': 'ir.actions.act_window_close'}
