# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta

class DentalLabOrder(models.Model):
    _name = 'dental.lab.order'
    _description = 'Dental Laboratory Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, due_date asc, id desc'

    name = fields.Char(
        string='Order Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Clinic / Branch',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Currency',
        readonly=True
    )

    # Patient & Clinical Links
    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        required=True,
        domain=[('is_dental_patient', '=', True)],
        tracking=True
    )
    patient_age = fields.Integer(
        string='Age',
        compute='_compute_patient_info'
    )
    patient_gender = fields.Selection(
        related='patient_id.gender',
        string='Gender',
        readonly=True
    )
    case_id = fields.Many2one(
        'dental.case',
        string='Dental Case',
        required=True,
        tracking=True,
        ondelete='restrict'
    )
    dentist_id = fields.Many2one(
        'hr.employee.public',
        string='Ordering Dentist',
        tracking=True,
        help='Dentist who prescribed this dental laboratory work.'
    )
    appointment_id = fields.Many2one(
        'dental.appointment',
        string='Appointment',
        tracking=True
    )
    treatment_plan_id = fields.Many2one(
        'dental.treatment.plan',
        string='Treatment Plan'
    )
    treatment_session_id = fields.Many2one(
        'dental.treatment.session',
        string='Treatment Session'
    )

    # Laboratory Logistics & Routing
    lab_type = fields.Selection([
        ('in_house', 'In-House Dental Laboratory'),
        ('external', 'External Commercial Laboratory'),
    ], string='Laboratory Routing', default='in_house', required=True, tracking=True)

    external_lab_id = fields.Many2one(
        'res.partner',
        string='External Lab Partner',
        domain="['|', ('is_company', '=', True), ('supplier_rank', '>', 0)]",
        tracking=True,
        help='External commercial dental laboratory vendor.'
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High Priority'),
        ('3', 'Urgent / Rush Order'),
    ], default='0', string='Priority', tracking=True)

    order_date = fields.Date(
        string='Order Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    due_date = fields.Date(
        string='Required Delivery Date',
        required=True,
        default=lambda self: fields.Date.context_today(self) + timedelta(days=5),
        tracking=True
    )
    promised_delivery_date = fields.Date(
        string='Promised Delivery Date',
        tracking=True
    )

    coordinator_id = fields.Many2one(
        'res.users',
        string='Lab Coordinator',
        default=lambda self: self.env.user,
        tracking=True
    )
    technician_id = fields.Many2one(
        'res.users',
        string='Assigned Technician',
        tracking=True,
        help='Certified technician responsible for fabrication / digital design.'
    )

    # Workflow Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted to Lab'),
        ('in_production', 'In Production'),
        ('qc_pending', 'QC Pending'),
        ('qc_approved', 'Quality Approved'),
        ('rework', 'In Rework / Defect Correction'),
        ('finished', 'Finished Goods Stored'),
        ('dispatched', 'Dispatched to Clinic'),
        ('received_clinic', 'Received at Clinic'),
        ('dentist_accepted', 'Dentist Clinically Accepted'),
        ('closed', 'Completed & Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # Impression & Case Specifications
    impression_type = fields.Selection([
        ('digital', 'Intraoral Digital Scan (STL/PLY/OBJ)'),
        ('physical_silicone', 'Physical PVS / Addition Silicone Impression'),
        ('physical_alginate', 'Physical Alginate Impression'),
        ('stone_model', 'Poured Master Stone Cast / Die Model'),
        ('bite_registration', 'Bite Registration Impression'),
        ('other', 'Other Impression Type'),
    ], string='Impression Format', default='digital', required=True)

    antagonist_impression = fields.Boolean(
        string='Antagonist Arch Included',
        default=True,
        help='Opposing arch scan or physical impression provided.'
    )
    bite_registration = fields.Boolean(
        string='Bite Registration Included',
        default=True,
        help='Interocclusal bite registration record supplied.'
    )
    articulators_included = fields.Boolean(
        string='Physical Articulator Sent',
        default=False
    )

    # Esthetics & Preparation Specs
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
    ], string='Target VITA Shade', default='A2')

    stump_shade = fields.Char(
        string='Stump / Prep Die Shade',
        help='Natural tooth preparation die shade (e.g., ND1, ND2, ND3, ND4, ND5...)'
    )
    margin_design = fields.Selection([
        ('chamfer', 'Deep Chamfer'),
        ('shoulder', 'Radial / 90° Shoulder'),
        ('feather', 'Feather / Knife Edge'),
        ('subgingival', 'Subgingival Margin (0.5mm)'),
        ('supragingival', 'Supragingival Margin'),
    ], string='Margin Preparation Design', default='chamfer')

    occlusal_clearance = fields.Selection([
        ('tight', 'Tight Contact (0.5 mm)'),
        ('normal', 'Standard Normal Contact (1.0 mm)'),
        ('light', 'Light Occlusal Contact (1.5 mm)'),
        ('out_of_occlusion', 'Completely Out of Occlusion'),
    ], string='Occlusal Clearance / Bite', default='normal')

    clinical_instructions = fields.Text(
        string='Dentist Clinical Prescription',
        help='Detailed clinical and technical prescription from the prescribing dentist.'
    )
    internal_technician_notes = fields.Text(
        string='Internal Technician / CAD Notes',
        help='Internal laboratory manufacturing observations, milling parameters, or sintering programs.'
    )

    # Attachments (STL files, DICOM, photos)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'dental_lab_order_attachment_rel',
        'order_id', 'attachment_id',
        string='Digital Scans & Clinical Images'
    )

    # Order Lines
    line_ids = fields.One2many(
        'dental.lab.order.line',
        'order_id',
        string='Tooth Restoration Lines'
    )
    tooth_summary = fields.Char(
        string='Teeth Involved',
        compute='_compute_tooth_summary',
        store=True
    )

    # Manufacturing Integration
    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        readonly=True,
        tracking=True
    )

    # Quality Integration
    quality_check_ids = fields.One2many(
        'quality.check',
        'lab_order_id',
        string='Quality Inspections'
    )
    quality_check_count = fields.Integer(
        string='Quality Checks Count',
        compute='_compute_quality_counts'
    )
    quality_alert_ids = fields.One2many(
        'quality.alert',
        'lab_order_id',
        string='Quality Alerts'
    )
    quality_alert_count = fields.Integer(
        string='Quality Alerts Count',
        compute='_compute_quality_counts'
    )

    # Dispatch & Receipt
    dispatch_ids = fields.One2many(
        'dental.lab.dispatch',
        'order_id',
        string='Dispatches'
    )
    dispatch_count = fields.Integer(
        string='Dispatch Count',
        compute='_compute_dispatch_receipt_counts'
    )
    receipt_ids = fields.One2many(
        'dental.lab.receipt',
        'order_id',
        string='Receipts'
    )
    receipt_count = fields.Integer(
        string='Receipt Count',
        compute='_compute_dispatch_receipt_counts'
    )

    # External Lab Tracking
    external_reference = fields.Char(string='External Lab Reference / Job #')
    external_quotation_cost = fields.Monetary(string='External Quotation / Fee')
    external_courier_name = fields.Char(string='Courier / Logistics Partner')
    external_tracking_number = fields.Char(string='Courier Tracking #')
    external_dispatch_date = fields.Date(string='Sent to External Lab On')
    external_expected_return = fields.Date(string='Expected Return from External Lab')
    external_actual_return = fields.Date(string='Received Back from External Lab')

    # Clinical Acceptance
    dentist_fit_rating = fields.Selection([
        ('excellent', 'Excellent (Passive Fit & Perfect Margins)'),
        ('good', 'Good (Minor Chairside Polish Needed)'),
        ('acceptable', 'Acceptable (Minor Contact Relief Done)'),
        ('poor', 'Poor Fit (Defective / Rejected)'),
    ], string='Clinical Fit & Seating')
    dentist_shade_match = fields.Selection([
        ('perfect', 'Perfect Shade & Esthetics Match'),
        ('acceptable', 'Clinically Acceptable Match'),
        ('mismatched', 'Mismatched (Requires Reglaze / Rework)'),
    ], string='Esthetics & Shade Verification')
    dentist_acceptance_notes = fields.Text(string='Dentist Clinical Verification Notes')
    dentist_accepted_by = fields.Many2one('res.users', string='Clinically Verified By', readonly=True)
    dentist_accepted_date = fields.Datetime(string='Clinical Acceptance Timestamp', readonly=True)

    # Costing & Financials
    material_cost = fields.Monetary(string='Material Consumption Cost', compute='_compute_costs', store=True)
    production_cost = fields.Monetary(string='In-House Production Cost', compute='_compute_costs', store=True)
    external_lab_cost = fields.Monetary(string='External Lab Charges', default=0.0)
    patient_billable_amount = fields.Monetary(string='Patient-Billable Lab Fee', compute='_compute_costs', store=True)
    is_invoiced = fields.Boolean(string='Invoiced to Patient', default=False)
    invoice_id = fields.Many2one('account.move', string='Customer Invoice', readonly=True)

    # -------------------------------------------------------------------------
    # Computes
    # -------------------------------------------------------------------------
    @api.depends('patient_id.date_of_birth')
    def _compute_patient_info(self):
        for order in self:
            if order.patient_id and hasattr(order.patient_id, 'age') and order.patient_id.age:
                order.patient_age = order.patient_id.age
            elif order.patient_id and order.patient_id.date_of_birth:
                from datetime import date
                from dateutil.relativedelta import relativedelta
                order.patient_age = relativedelta(date.today(), order.patient_id.date_of_birth).years
            else:
                order.patient_age = 0

    @api.depends('line_ids.tooth_number')
    def _compute_tooth_summary(self):
        for order in self:
            teeth = [line.tooth_number for line in order.line_ids if line.tooth_number]
            order.tooth_summary = ", ".join(teeth) if teeth else _("Full Arch / Appliance")

    @api.depends('quality_check_ids', 'quality_alert_ids')
    def _compute_quality_counts(self):
        for order in self:
            order.quality_check_count = len(order.quality_check_ids)
            order.quality_alert_count = len(order.quality_alert_ids)

    @api.depends('dispatch_ids', 'receipt_ids')
    def _compute_dispatch_receipt_counts(self):
        for order in self:
            order.dispatch_count = len(order.dispatch_ids)
            order.receipt_count = len(order.receipt_ids)

    @api.depends('line_ids.subtotal', 'external_lab_cost', 'production_id.cost_factor' if hasattr(models.Model, 'cost_factor') else 'line_ids')
    def _compute_costs(self):
        for order in self:
            total_billable = sum(order.line_ids.mapped('subtotal'))
            order.patient_billable_amount = total_billable
            if order.lab_type == 'external':
                order.material_cost = 0.0
                order.production_cost = order.external_lab_cost
            else:
                # Estimate material cost from line products cost price
                order.material_cost = sum(line.product_id.standard_price * line.quantity for line in order.line_ids if line.product_id)
                order.production_cost = order.material_cost * 1.5

    # -------------------------------------------------------------------------
    # Lifecycle & Validation
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.lab.order') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        for order in self:
            if not order.line_ids:
                raise ValidationError(_("Cannot submit an empty Lab Order. Please add at least one tooth restoration line."))
            if order.lab_type == 'external' and not order.external_lab_id:
                raise ValidationError(_("Please select an External Lab Partner before submitting."))
            order.write({'state': 'submitted'})
            order.line_ids.write({'state': 'in_production'})
            order.message_post(
                body=_("Lab Order submitted successfully. Ready for technician scheduling / external dispatch."),
                message_type='notification'
            )

    def action_start_production(self):
        for order in self:
            if order.state not in ('submitted', 'rework'):
                raise UserError(_("Order must be in Submitted or Rework state to begin production."))

            if order.lab_type == 'in_house':
                # Check if we should generate an MRP Production Order
                order._create_or_link_mrp_production()
            else:
                order.external_dispatch_date = fields.Date.context_today(order)

            order.write({'state': 'in_production'})
            order.line_ids.write({'state': 'in_production'})
            order.message_post(
                body=_("Production commenced. Materials allocated."),
                message_type='notification'
            )

    def _create_or_link_mrp_production(self):
        self.ensure_one()
        if self.production_id:
            return self.production_id

        # Look for the first product with a BOM
        target_product = False
        target_bom = False
        for line in self.line_ids:
            if line.product_id:
                bom = self.env['mrp.bom'].search([
                    '|',
                    ('product_id', '=', line.product_id.id),
                    ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)
                ], limit=1)
                if bom:
                    target_product = line.product_id
                    target_bom = bom
                    break

        if not target_product and self.line_ids and self.line_ids[0].product_id:
            target_product = self.line_ids[0].product_id

        if target_product:
            mo_vals = {
                'product_id': target_product.id,
                'product_qty': sum(self.line_ids.mapped('quantity')) or 1.0,
                'product_uom_id': target_product.uom_id.id,
                'bom_id': target_bom.id if target_bom else False,
                'origin': self.name,
                'company_id': self.company_id.id,
                'lab_order_id': self.id,
            }
            try:
                mo = self.env['mrp.production'].create(mo_vals)
                mo.action_confirm()
                self.production_id = mo.id
                return mo
            except Exception as e:
                # If BOM is missing or routing fails, log message but allow manual in-house tracking
                self.message_post(body=_("Note: Manufacturing order creation skipped: %s", str(e)))
        return False

    def action_request_qc(self):
        """Trigger Quality Control Inspections using the existing Quality module."""
        for order in self:
            if order.state not in ('in_production', 'rework'):
                raise UserError(_("Quality Inspection can only be triggered while in Production or Rework."))

            order._generate_dental_quality_checks()
            order.write({'state': 'qc_pending'})
            order.line_ids.write({'state': 'qc_pending'})
            order.message_post(
                body=_("Quality inspection requested. Pending evaluation by authorized Quality Inspector."),
                message_type='comment'
            )

    def _generate_dental_quality_checks(self):
        self.ensure_one()
        # Find matching quality control points from Quality module
        products = self.line_ids.mapped('product_id')
        points = self.env['quality.point']._get_matching_points(
            company=self.company_id,
            products=products,
            is_manufacturing=True,
        )

        checks_created = self.env['quality.check']
        existing_check_titles = self.quality_check_ids.mapped('title')

        # 1. If control points exist in Quality module, use them
        if points:
            common_vals = {
                'lab_order_id': self.id,
                'company_id': self.company_id.id,
            }
            checks_created |= self.env['quality.check']._create_checks_from_points(
                points, common_vals, products=products
            )

        # 2. Also ensure standard dental laboratory quality criteria are checked
        stages = [
            ('prescription', _("Prescription & Tooth Specification Compliance"),
             _("Verify that the restoration matches the requested tooth numbers (%s), shade (%s), and doctor instructions.") % (self.tooth_summary, self.shade)),
            ('dimensions', _("Margin Fit & Die Seating"),
             _("Check that marginal seal is airtight (no open margins) and fits stone die/digital scan passively without rocking.")),
            ('shade', _("Shade & Esthetics Match"),
             _("Verify color match under 5500K daylight lamp against VITA shade %s with correct cervical/incisal translucency.") % self.shade),
            ('surface', _("Surface Polish, Contacts & Occlusion"),
             _("Ensure all surfaces are glazed/polished to high luster with proper interproximal contact and occlusal clearance (%s).") % self.occlusal_clearance),
            ('disinfection', _("Ultrasonic Cleaning, Disinfection & Sealed Packaging"),
             _("Ensure restoration has been ultrasonically cleaned, clinically disinfected, and heat-sealed in an authorized pouch.")),
        ]

        default_team = self.env['quality.team'].search([], limit=1)
        for stage_code, title, instructions in stages:
            if title in existing_check_titles:
                continue
            first_line = self.line_ids[:1]
            prod = first_line.product_id if first_line else False
            check_vals = {
                'title': title,
                'lab_order_id': self.id,
                'lab_order_line_id': first_line.id if first_line else False,
                'product_id': prod.id if prod else False,
                'company_id': self.company_id.id,
                'team_id': default_team.id if default_team else False,
                'user_id': self.env.user.id,
                'test_type': 'passfail',
                'dental_inspection_stage': stage_code,
                'instructions': "<p>%s</p>" % instructions,
                'quality_state': 'none',
            }
            checks_created |= self.env['quality.check'].create(check_vals)

        return checks_created

    def _check_all_qc_status(self):
        self.ensure_one()
        all_checks = self.quality_check_ids
        if not all_checks:
            return

        any_failed = any(c.quality_state == 'fail' for c in all_checks)
        all_passed = all(c.quality_state == 'pass' for c in all_checks)

        if any_failed:
            self.write({'state': 'rework'})
        elif all_passed:
            self.write({'state': 'qc_approved'})
            self.line_ids.write({'state': 'qc_passed'})
            self.message_post(
                body=_("<b>Quality Approved:</b> All laboratory quality checks have successfully passed! Ready for finished goods storage / dispatch."),
                message_type='notification'
            )

    def action_receive_finished_goods(self):
        for order in self:
            if order.state != 'qc_approved':
                raise UserError(_("Finished goods can only be released after all Quality Inspections are Approved."))
            order.write({'state': 'finished'})
            order.line_ids.write({'state': 'completed'})
            order.message_post(
                body=_("Finished goods inspected and received into finished laboratory inventory."),
                message_type='notification'
            )

    def action_create_dispatch(self):
        self.ensure_one()
        if self.state not in ('qc_approved', 'finished'):
            raise UserError(_("Cannot dispatch work that has not passed Quality Control."))

        dispatch = self.env['dental.lab.dispatch'].create({
            'order_id': self.id,
            'dispatch_date': fields.Datetime.now(),
            'sender_id': self.env.user.id,
            'destination_clinic_id': self.company_id.id,
            'delivery_method': 'internal_runner' if self.lab_type == 'in_house' else 'courier',
            'courier_name': self.external_courier_name,
            'tracking_reference': self.external_tracking_number,
        })
        self.write({'state': 'dispatched'})
        return {
            'name': _('Dispatch Delivery Record'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.dispatch',
            'view_mode': 'form',
            'res_id': dispatch.id,
        }

    def action_receive_at_clinic(self):
        self.ensure_one()
        if self.state != 'dispatched':
            raise UserError(_("Order must be Dispatched before it can be Received at the clinic."))

        latest_dispatch = self.dispatch_ids[:1]
        receipt = self.env['dental.lab.receipt'].create({
            'order_id': self.id,
            'dispatch_id': latest_dispatch.id if latest_dispatch else False,
            'receipt_date': fields.Datetime.now(),
            'receiver_id': self.env.user.id,
            'condition': 'intact',
            'quantity_received': sum(self.line_ids.mapped('quantity')) or 1.0,
        })
        self.write({'state': 'received_clinic'})
        return {
            'name': _('Clinic Receipt Record'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.receipt',
            'view_mode': 'form',
            'res_id': receipt.id,
        }

    def action_record_dentist_acceptance(self):
        for order in self:
            if order.state != 'received_clinic':
                raise UserError(_("Work must be received at clinic before clinical acceptance can be recorded."))

            # Enforce dentist role
            is_dentist = (
                self.env.user.has_group('dental_base.group_dental_dentist') or
                self.env.user.has_group('dental_base.group_dental_manager') or
                self.env.user.has_group('dental_base.group_dental_admin') or
                self.env.is_superuser()
            )
            if not is_dentist:
                raise UserError(_("Only authorized Dentists or Clinic Managers can record clinical acceptance."))

            if order.dentist_fit_rating == 'poor' or order.dentist_shade_match == 'mismatched':
                raise UserError(_("Cannot accept work when Fit is Poor or Shade is Mismatched. Please initiate Rework instead."))

            order.write({
                'state': 'dentist_accepted',
                'dentist_accepted_by': self.env.user.id,
                'dentist_accepted_date': fields.Datetime.now(),
            })
            order.message_post(
                body=_("<b>Dentist Clinical Acceptance Confirmed:</b> Fit: %s, Shade: %s.<br/>Notes: %s") % (
                    order.dentist_fit_rating or _("Good"),
                    order.dentist_shade_match or _("Acceptable"),
                    order.dentist_acceptance_notes or _("No clinical adjustments needed.")
                ),
                message_type='comment'
            )

    def action_close_order(self):
        for order in self:
            if order.state != 'dentist_accepted':
                raise UserError(_("Cannot close Dental Lab Order: Clinical acceptance by the treating dentist is mandatory before closure."))
            order.write({'state': 'closed'})
            order.message_post(
                body=_("Dental Laboratory Order successfully closed and archived."),
                message_type='notification'
            )

    def action_request_rework(self):
        self.ensure_one()
        return {
            'name': _('Request Laboratory Rework'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.rework.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_rework_reason': self.dentist_acceptance_notes or '',
            }
        }

    def action_cancel(self):
        for order in self:
            if order.state in ('dentist_accepted', 'closed'):
                raise UserError(_("Cannot cancel an order that has already been clinically accepted or closed."))
            order.write({'state': 'cancelled'})
            order.line_ids.write({'state': 'cancelled'})
            if order.production_id and order.production_id.state not in ('done', 'cancel'):
                order.production_id.action_cancel()

    def action_reopen(self):
        for order in self:
            order.write({'state': 'draft'})

    def _on_mrp_production_done(self, production):
        self.ensure_one()
        if self.state == 'in_production':
            # Check if all QC checks passed
            self._check_all_qc_status()

    # Smart Button Actions
    def action_view_quality_checks(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('Quality.action_quality_check')
        action['domain'] = [('lab_order_id', '=', self.id)]
        action['context'] = {
            'default_lab_order_id': self.id,
            'default_company_id': self.company_id.id,
        }
        return action

    def action_view_quality_alerts(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('Quality.action_quality_alert')
        action['domain'] = [('lab_order_id', '=', self.id)]
        action['context'] = {
            'default_lab_order_id': self.id,
            'default_company_id': self.company_id.id,
        }
        return action

    def action_view_mrp_production(self):
        self.ensure_one()
        return {
            'name': _('Manufacturing Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.production_id.id,
        }

    def action_view_dispatches(self):
        self.ensure_one()
        return {
            'name': _('Dispatches for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.dispatch',
            'view_mode': 'list,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def action_view_receipts(self):
        self.ensure_one()
        return {
            'name': _('Receipts for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.receipt',
            'view_mode': 'list,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }
