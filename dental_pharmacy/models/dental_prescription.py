# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class DentalPrescription(models.Model):
    _name = 'dental.prescription'
    _description = 'Dental Clinical Prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'prescription_date desc, id desc'

    name = fields.Char(
        string='Prescription Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        required=True,
        domain=[('is_dental_patient', '=', True)],
        tracking=True,
        index=True
    )
    patient_dental_id = fields.Char(
        string='Patient ID',
        related='patient_id.dental_patient_id',
        readonly=True
    )
    patient_age = fields.Integer(
        string='Age',
        related='patient_id.age',
        readonly=True
    )
    patient_gender = fields.Selection(
        string='Gender',
        related='patient_id.gender',
        readonly=True
    )
    patient_phone = fields.Char(
        string='Phone',
        related='patient_id.phone',
        readonly=True
    )
    patient_allergies = fields.Html(
        string='Allergies & Medical Alerts',
        related='patient_id.allergies',
        readonly=True
    )
    dentist_id = fields.Many2one(
        'hr.employee',
        string='Prescribing Dentist',
        required=True,
        domain="[('is_dentist', '=', True)]",
        default=lambda self: self._default_dentist_id(),
        tracking=True,
        index=True
    )
    dentist_reg_no = fields.Char(
        string='License / Reg No.',
        related='dentist_id.registration_number',
        readonly=True
    )
    dentist_specialization = fields.Char(
        string='Specialization',
        related='dentist_id.specialization',
        readonly=True
    )
    dentist_signature = fields.Binary(
        string='Doctor Signature',
        related='dentist_id.signature_image',
        readonly=True
    )
    case_id = fields.Many2one(
        'dental.case',
        string='Dental Case',
        domain="[('patient_id', '=', patient_id)]",
        tracking=True,
        index=True
    )
    appointment_id = fields.Many2one(
        'dental.appointment',
        string='Related Appointment',
        domain="[('patient_id', '=', patient_id)]",
        tracking=True
    )
    prescription_date = fields.Date(
        string='Prescription Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    diagnosis = fields.Char(
        string='Indication / Diagnosis',
        tracking=True,
        help='Primary diagnosis or clinical reason for prescribing (e.g., Acute Apical Periodontitis, Post-Op Pain)'
    )
    clinical_notes = fields.Text(
        string='Clinical Advice / Special Instructions',
        help='Advice given to patient regarding diet, rest, hygiene, or warnings.'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('partially_dispensed', 'Partially Dispensed'),
        ('fully_dispensed', 'Fully Dispensed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, index=True)

    line_ids = fields.One2many(
        'dental.prescription.line',
        'prescription_id',
        string='Prescribed Medicines',
        copy=True
    )
    dispense_ids = fields.One2many(
        'dental.pharmacy.dispense',
        'prescription_id',
        string='Dispensing Records'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Clinic Branch',
        default=lambda self: self.env.company,
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True
    )
    total_prescribed_qty = fields.Float(
        string='Total Prescribed Qty',
        compute='_compute_quantities',
        store=True
    )
    total_dispensed_qty = fields.Float(
        string='Total Dispensed Qty',
        compute='_compute_quantities',
        store=True
    )
    total_remaining_qty = fields.Float(
        string='Total Remaining Qty',
        compute='_compute_quantities',
        store=True
    )
    dispense_count = fields.Integer(
        string='Dispense Count',
        compute='_compute_dispense_count'
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count'
    )

    def _default_dentist_id(self):
        employee = self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.env.uid),
            ('is_dentist', '=', True)
        ], limit=1)
        if not employee:
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', self.env.uid)
            ], limit=1)
        return employee.id if employee else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.prescription') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.quantity', 'line_ids.dispensed_qty')
    def _compute_quantities(self):
        for rx in self:
            prescribed = sum(rx.line_ids.mapped('quantity'))
            dispensed = sum(rx.line_ids.mapped('dispensed_qty'))
            rx.total_prescribed_qty = prescribed
            rx.total_dispensed_qty = dispensed
            rx.total_remaining_qty = max(0.0, prescribed - dispensed)

    def _compute_dispense_count(self):
        for rx in self:
            rx.dispense_count = len(rx.dispense_ids)

    def _compute_invoice_count(self):
        for rx in self:
            invoices = rx.dispense_ids.mapped('invoice_id').filtered(lambda inv: inv)
            rx.invoice_count = len(invoices)

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id and self.case_id and self.case_id.patient_id != self.patient_id:
            self.case_id = False
        if self.patient_id and self.appointment_id and self.appointment_id.patient_id != self.patient_id:
            self.appointment_id = False

    def action_confirm(self):
        for record in self:
            # Security verification
            if not (self.env.user.has_group('dental_base.group_dental_dentist') or
                    self.env.user.has_group('dental_base.group_dental_manager') or
                    self.env.user.has_group('dental_base.group_dental_admin')):
                raise ValidationError(_("Only dentists and clinic managers are authorized to confirm clinical prescriptions."))

            if not record.line_ids:
                raise ValidationError(_("Please add at least one medicine before confirming the prescription."))

            for line in record.line_ids:
                if line.quantity <= 0:
                    raise ValidationError(_("Prescribed quantity for %s must be greater than zero.") % line.medicine_id.display_name)

            record.state = 'confirmed'
            record.message_post(body=_("Prescription confirmed by %s.") % self.env.user.name)

    def action_cancel(self):
        for record in self:
            if record.total_dispensed_qty > 0:
                raise UserError(_("Cannot cancel prescription %s because medicines have already been dispensed. "
                                  "Authorized returns must be processed in the Dispensing module first.") % record.name)
            record.state = 'cancelled'
            record.message_post(body=_("Prescription cancelled by %s.") % self.env.user.name)

    def action_draft(self):
        for record in self:
            if record.total_dispensed_qty > 0:
                raise UserError(_("Cannot reset to draft because medications have already been dispensed."))
            record.state = 'draft'

    def _update_dispensing_state(self):
        for rx in self:
            self._compute_quantities()
            if rx.state == 'cancelled':
                continue
            if rx.total_dispensed_qty == 0:
                rx.state = 'confirmed'
            elif rx.total_remaining_qty <= 0:
                rx.state = 'fully_dispensed'
            else:
                rx.state = 'partially_dispensed'

    def action_dispense(self):
        self.ensure_one()
        if self.state not in ('confirmed', 'partially_dispensed'):
            raise UserError(_("Only confirmed or partially dispensed prescriptions can be dispensed."))
        if self.total_remaining_qty <= 0:
            raise UserError(_("All prescribed items for this prescription have already been fully dispensed."))

        return {
            'name': _('Dispense Prescription %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.pharmacy.dispense',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_prescription_id': self.id,
                'default_company_id': self.company_id.id,
            }
        }

    def action_view_dispenses(self):
        self.ensure_one()
        return {
            'name': _('Dispensing Records for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.pharmacy.dispense',
            'view_mode': 'list,form',
            'domain': [('prescription_id', '=', self.id)],
            'context': {'default_prescription_id': self.id},
        }

    def action_view_invoices(self):
        self.ensure_one()
        invoice_ids = self.dispense_ids.mapped('invoice_id').ids
        return {
            'name': _('Linked Invoices for %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
        }
