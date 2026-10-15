# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class QualityCheck(models.Model):
    _inherit = 'quality.check'

    lab_order_id = fields.Many2one(
        'dental.lab.order',
        string='Dental Lab Order',
        ondelete='cascade',
        index=True,
        tracking=True,
        help='Patient lab order associated with this quality inspection.'
    )
    lab_order_line_id = fields.Many2one(
        'dental.lab.order.line',
        string='Dental Lab Order Line',
        ondelete='set null',
        index=True,
        help='Tooth-specific restoration line being inspected.'
    )
    dental_inspection_stage = fields.Selection([
        ('prescription', '1. Prescription & Specification Compliance'),
        ('dimensions', '2. Marginal Fit, Die Seating & Dimensions'),
        ('shade', '3. Shade, Translucency & Esthetics'),
        ('surface', '4. Surface Finish, Occlusion & Contacts'),
        ('disinfection', '5. Ultrasonic Cleaning, Disinfection & Sealed Packaging'),
        ('external_incoming', 'External Lab Incoming Verification'),
        ('other', 'General Laboratory Inspection'),
    ], string='Dental QC Stage', default='prescription')

    is_rework = fields.Boolean(
        string='Is Rework Check',
        default=False,
        help='Flag indicating this check is a re-inspection following rework/defect correction.'
    )
    parent_check_id = fields.Many2one(
        'quality.check',
        string='Original Failed Inspection',
        readonly=True,
        help='Reference to the original check that failed before rework.'
    )
    rework_check_ids = fields.One2many(
        'quality.check',
        'parent_check_id',
        string='Re-inspections'
    )
    rework_reason = fields.Text(
        string='Rework Instructions / Defect Details',
        help='Corrective feedback provided by the QC Inspector for the lab technician.'
    )

    def do_pass(self):
        self._check_qc_permission()
        res = super().do_pass()
        for check in self:
            if check.lab_order_line_id:
                check.lab_order_line_id.write({
                    'state': 'qc_passed',
                    'quality_check_id': check.id,
                })
            if check.lab_order_id:
                check.lab_order_id._check_all_qc_status()
        return res

    def do_fail(self, failure_location_id=False):
        self._check_qc_permission()
        res = super().do_fail(failure_location_id=failure_location_id)
        for check in self:
            if check.lab_order_line_id:
                check.lab_order_line_id.write({
                    'state': 'qc_failed',
                    'quality_check_id': check.id,
                })
            if check.lab_order_id:
                check.lab_order_id.write({'state': 'rework'})
                check.lab_order_id.message_post(
                    body=_("<b>Quality Inspection FAILED:</b> %s.<br/>Defect Details: %s") % (
                        check.title or check.name,
                        check.failure_message or check.notes or _("Check failed specifications.")
                    ),
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
        return res

    def _create_alert_from_failure(self):
        alerts = super()._create_alert_from_failure()
        for check in self:
            matched_alerts = alerts.filtered(lambda a: a.check_id.id == check.id)
            if matched_alerts and check.lab_order_id:
                matched_alerts.write({
                    'lab_order_id': check.lab_order_id.id,
                    'lab_order_line_id': check.lab_order_line_id.id if check.lab_order_line_id else False,
                })
        return alerts

    def _check_qc_permission(self):
        """Enforce role-based quality control: Only authorized Quality users or Lab Managers can pass/fail."""
        has_qc_group = (
            self.env.user.has_group('Quality.group_quality_user') or
            self.env.user.has_group('Quality.group_quality_manager') or
            self.env.user.has_group('dental_lab.group_dental_lab_manager') or
            self.env.user.has_group('dental_base.group_dental_admin') or
            self.env.is_superuser()
        )
        if not has_qc_group:
            raise UserError(_("Access Denied: Only certified Quality Inspectors or Lab Managers can validate Quality Checks."))

    def action_initiate_rework(self):
        self.ensure_one()
        return {
            'name': _('Initiate Rework / Defect Correction'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.rework.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_check_id': self.id,
                'default_order_id': self.lab_order_id.id if self.lab_order_id else False,
                'default_order_line_id': self.lab_order_line_id.id if self.lab_order_line_id else False,
                'default_rework_reason': self.failure_message or self.notes or '',
            }
        }
