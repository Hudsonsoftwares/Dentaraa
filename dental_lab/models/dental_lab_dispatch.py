# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DentalLabDispatch(models.Model):
    _name = 'dental.lab.dispatch'
    _description = 'Dental Laboratory Dispatch Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'dispatch_date desc, id desc'

    name = fields.Char(
        string='Dispatch Reference',
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
    dispatch_date = fields.Datetime(
        string='Dispatched Timestamp',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    sender_id = fields.Many2one(
        'res.users',
        string='Dispatched By',
        default=lambda self: self.env.user,
        tracking=True
    )
    delivery_method = fields.Selection([
        ('internal_runner', 'Internal Clinic Runner / Staff'),
        ('courier', 'Commercial Courier Logistics'),
        ('clinic_pickup', 'Dentist / Clinic Pickup'),
    ], string='Delivery Method', default='internal_runner', required=True)

    courier_name = fields.Char(string='Courier Service Provider')
    tracking_reference = fields.Char(string='Airway Bill / Tracking #')
    destination_clinic_id = fields.Many2one(
        'res.company',
        string='Destination Clinic',
        default=lambda self: self.env.company
    )
    notes = fields.Text(string='Dispatch Notes / Handling Precautions')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_transit', 'In Transit / Dispatched'),
        ('delivered', 'Delivered to Clinic'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='in_transit', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.lab.dispatch') or _('New')
        return super().create(vals_list)

    def action_mark_delivered(self):
        for rec in self:
            rec.write({'state': 'delivered'})
            if rec.order_id and rec.order_id.state == 'dispatched':
                rec.order_id.action_receive_at_clinic()
