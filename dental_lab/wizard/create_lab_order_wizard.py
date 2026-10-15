# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta

class DentalLabCreateWizard(models.TransientModel):
    _name = 'dental.lab.create.wizard'
    _description = 'Wizard to Create Patient Dental Lab Order'

    case_id = fields.Many2one('dental.case', string='Dental Case', required=True)
    patient_id = fields.Many2one('res.partner', string='Patient', required=True)
    dentist_id = fields.Many2one('hr.employee.public', string='Dentist')
    appointment_id = fields.Many2one('dental.appointment', string='Appointment')
    company_id = fields.Many2one('res.company', string='Clinic Branch', default=lambda self: self.env.company)

    existing_order_count = fields.Integer(string='Existing Active Orders', compute='_compute_existing_orders')
    existing_order_id = fields.Many2one('dental.lab.order', string='Existing Order', compute='_compute_existing_orders')
    existing_order_warning = fields.Html(string='Duplicate Prevention Notice', compute='_compute_existing_orders')

    lab_type = fields.Selection([
        ('in_house', 'In-House Dental Laboratory'),
        ('external', 'External Commercial Laboratory'),
    ], string='Laboratory Routing', default='in_house', required=True)

    external_lab_id = fields.Many2one(
        'res.partner',
        string='External Lab Partner',
        domain="['|', ('is_company', '=', True), ('supplier_rank', '>', 0)]"
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High Priority'),
        ('3', 'Urgent / Rush Order'),
    ], default='0', string='Priority')

    due_date = fields.Date(
        string='Required Delivery Date',
        required=True,
        default=lambda self: fields.Date.context_today(self) + timedelta(days=5)
    )

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
    ], string='Target Shade', default='A2')

    stump_shade = fields.Char(string='Stump Die Shade')
    margin_design = fields.Selection([
        ('chamfer', 'Deep Chamfer'),
        ('shoulder', 'Radial / 90° Shoulder'),
        ('feather', 'Feather / Knife Edge'),
        ('subgingival', 'Subgingival Margin (0.5mm)'),
        ('supragingival', 'Supragingival Margin'),
    ], string='Margin Design', default='chamfer')

    occlusal_clearance = fields.Selection([
        ('tight', 'Tight Contact (0.5 mm)'),
        ('normal', 'Standard Normal Contact (1.0 mm)'),
        ('light', 'Light Occlusal Contact (1.5 mm)'),
        ('out_of_occlusion', 'Completely Out of Occlusion'),
    ], string='Occlusal Clearance', default='normal')

    clinical_instructions = fields.Text(string='Prescription / Instructions')
    line_ids = fields.One2many('dental.lab.create.wizard.line', 'wizard_id', string='Tooth Restorations')

    @api.depends('case_id')
    def _compute_existing_orders(self):
        for wiz in self:
            if wiz.case_id:
                active_orders = self.env['dental.lab.order'].search([
                    ('case_id', '=', wiz.case_id.id),
                    ('state', 'not in', ('closed', 'cancelled'))
                ])
                wiz.existing_order_count = len(active_orders)
                wiz.existing_order_id = active_orders[:1].id if active_orders else False
                if active_orders:
                    order_refs = ", ".join(active_orders.mapped('name'))
                    wiz.existing_order_warning = _(
                        "<div class='alert alert-warning mb-0'>"
                        "<strong>Notice:</strong> An active lab order (<b>%s</b>) is already registered for Dental Case <b>%s</b>. "
                        "You may open the existing order or proceed to create an intentional separate order.</div>"
                    ) % (order_refs, wiz.case_id.name)
                else:
                    wiz.existing_order_warning = False
            else:
                wiz.existing_order_count = 0
                wiz.existing_order_id = False
                wiz.existing_order_warning = False

    def action_open_existing(self):
        self.ensure_one()
        if not self.existing_order_id:
            raise UserError(_("No active existing lab order found."))
        return {
            'name': _('Dental Lab Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'form',
            'res_id': self.existing_order_id.id,
        }

    def action_confirm_create(self):
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError(_("Please specify at least one tooth restoration line for the laboratory order."))
        if self.lab_type == 'external' and not self.external_lab_id:
            raise ValidationError(_("Please select an External Lab Partner."))

        order_vals = {
            'case_id': self.case_id.id,
            'patient_id': self.patient_id.id,
            'dentist_id': self.dentist_id.id if self.dentist_id else False,
            'appointment_id': self.appointment_id.id if self.appointment_id else False,
            'company_id': self.company_id.id,
            'lab_type': self.lab_type,
            'external_lab_id': self.external_lab_id.id if self.external_lab_id else False,
            'priority': self.priority,
            'due_date': self.due_date,
            'shade': self.shade,
            'stump_shade': self.stump_shade,
            'margin_design': self.margin_design,
            'occlusal_clearance': self.occlusal_clearance,
            'clinical_instructions': self.clinical_instructions,
            'line_ids': [
                (0, 0, {
                    'tooth_number': line.tooth_number,
                    'restoration_type': line.restoration_type,
                    'product_id': line.product_id.id if line.product_id else False,
                    'material': line.material,
                    'shade': line.shade or self.shade,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'technical_notes': line.technical_notes,
                }) for line in self.line_ids
            ]
        }

        lab_order = self.env['dental.lab.order'].create(order_vals)

        return {
            'name': _('Dental Lab Order: %s', lab_order.name),
            'type': 'ir.actions.act_window',
            'res_model': 'dental.lab.order',
            'view_mode': 'form',
            'res_id': lab_order.id,
        }


class DentalLabCreateWizardLine(models.TransientModel):
    _name = 'dental.lab.create.wizard.line'
    _description = 'Wizard Line for Dental Lab Order Creation'

    wizard_id = fields.Many2one('dental.lab.create.wizard', required=True, ondelete='cascade')
    tooth_number = fields.Char(string='FDI Tooth / Range', required=True, default='11')
    restoration_type = fields.Selection([
        ('crown', 'Full Crown'),
        ('bridge', 'Multi-Unit Bridge'),
        ('inlay_onlay', 'Inlay / Onlay'),
        ('veneer', 'Veneer / Laminate'),
        ('denture_complete', 'Complete Denture (Full Arch)'),
        ('denture_partial', 'Cast Partial / Acrylic Denture'),
        ('implant_abutment', 'Custom Titanium / Zirconia Abutment'),
        ('implant_crown', 'Screw-Retained Implant Crown'),
        ('ortho_appliance', 'Orthodontic Appliance / Expander'),
        ('nightguard', 'Nightguard / Bruxism Splint'),
        ('retainer', 'Clear Retainer (Essix / Hawley)'),
        ('surgical_guide', '3D Printed Surgical Guide'),
        ('custom_tray', 'Custom Impression Tray'),
        ('other', 'Other Dental Appliance'),
    ], string='Restoration Type', required=True, default='crown')

    product_id = fields.Many2one('product.product', string='Catalog Product', domain="[('is_dental_lab_item', '=', True)]")
    material = fields.Selection([
        ('zirconia_ml', 'Zirconia Multilayer 3D Pro'),
        ('zirconia_mono', 'Zirconia Monolithic High Translucency'),
        ('emax_press', 'Lithium Disilicate (IPS E.max Press)'),
        ('emax_cad', 'IPS E.max CAD Block'),
        ('pfm', 'Porcelain Fused to Metal (PFM)'),
        ('cocr_alloy', 'Cobalt-Chromium Alloy (Co-Cr)'),
        ('nicr_alloy', 'Nickel-Chromium Alloy (Ni-Cr)'),
        ('titanium', 'Grade 5 Medical Titanium'),
        ('peek', 'PEEK High Performance Polymer'),
        ('pmma', 'PMMA Temp Block (CAD/CAM)'),
        ('acrylic', 'Heat-Cured Denture Acrylic'),
        ('valplast', 'Flexible Polyamide (Valplast)'),
        ('resin_3d', 'Light-Cure 3D Printing Resin'),
        ('other', 'Other Custom Material'),
    ], string='Material', default='zirconia_ml')

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
    ], string='Shade', default='A2')

    quantity = fields.Float(string='Units', default=1.0)
    unit_price = fields.Float(string='Price')
    technical_notes = fields.Char(string='Notes')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.list_price
            if self.product_id.dental_shade:
                self.shade = self.product_id.dental_shade
            if self.product_id.dental_material_composition:
                self.material = self.product_id.dental_material_composition
