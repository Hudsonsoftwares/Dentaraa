# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DentalLabReceipt(models.Model):
    _name = 'dental.lab.receipt'
    _description = 'Clinic Laboratory Receipt Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'receipt_date desc, id desc'

    name = fields.Char(
        string='Receipt Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    order_id = fields.Many2one(
        'dental.lab.order',
        string='Dental Lab Order',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    dispatch_id = fields.Many2one(
        'dental.lab.dispatch',
        string='Originating Dispatch',
        tracking=True
    )
    patient_id = fields.Many2one(
        'res.partner',
        related='order_id.patient_id',
        string='Patient',
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        related='order_id.company_id',
        string='Clinic Branch',
        store=True
    )
    receipt_date = fields.Datetime(
        string='Received Timestamp',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    receiver_id = fields.Many2one(
        'res.users',
        string='Received By (Staff)',
        default=lambda self: self.env.user,
        tracking=True
    )
    condition = fields.Selection([
        ('intact', 'Intact & In Perfect Condition'),
        ('damaged', 'Damaged in Transit'),
        ('incomplete', 'Incomplete / Missing Components'),
        ('rejected', 'Rejected at Clinic Reception'),
    ], string='Package Physical Condition', default='intact', required=True, tracking=True)

    package_sterility = fields.Selection([
        ('sterilized_sealed', 'Sterilized & Heat-Sealed Pouch'),
        ('disinfected', 'Clinically Disinfected & Wrapped'),
        ('unsealed', 'Unsealed / Requires Chairside Disinfection'),
    ], string='Sterility / Hygiene Status', default='sterilized_sealed', required=True)

    quantity_received = fields.Float(
        string='Units Received',
        default=1.0,
        required=True
    )
    discrepancy_notes = fields.Text(
        string='Discrepancy / Damage Notes',
        help='Record any physical damage, broken margins, missing dies, or transport issues.'
    )
    state = fields.Selection([
        ('received', 'Received at Clinic'),
        ('verified', 'Verified with Dentist'),
        ('returned', 'Returned to Lab for Correction'),
    ], string='Status', default='received', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.lab.receipt') or _('New')
        return super().create(vals_list)

    def action_verify_with_dentist(self):
        for rec in self:
            rec.write({'state': 'verified'})
            if rec.order_id and rec.order_id.state == 'received_clinic':
                rec.order_id.message_post(
                    body=_("Restoration received and verified by clinic staff (%s). Ready for dentist clinical seating.") % rec.receiver_id.name
                )
