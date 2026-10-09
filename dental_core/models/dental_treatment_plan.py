from odoo import models, fields, api, _

class DentalTreatmentPlan(models.Model):
    _name = 'dental.treatment.plan'
    _description = 'Treatment Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    case_id = fields.Many2one('dental.case', string='Dental Case', tracking=True)
    doctor_id = fields.Many2one('hr.employee', string='Doctor', tracking=True)
    appointment_id = fields.Many2one('dental.appointment', string='Appointment', tracking=True)
    branch_id = fields.Many2one('res.company', string='Branch', related='appointment_id.branch_id', store=True)
    
    plan_date = fields.Date(string='Plan Date', default=fields.Date.context_today, required=True, tracking=True)
    notes = fields.Text(string='Notes')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    line_ids = fields.One2many('dental.treatment.plan.line', 'plan_id', string='Treatments')
    estimated_total = fields.Monetary(string='Estimated Total', compute='_compute_total', store=True)
    currency_id = fields.Many2one('res.currency', related='branch_id.currency_id', depends=['branch_id.currency_id'], store=True)

    @api.depends('line_ids.estimated_amount')
    def _compute_total(self):
        for plan in self:
            plan.estimated_total = sum(plan.line_ids.mapped('estimated_amount'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.treatment.plan') or _('New')
        return super().create(vals_list)

class DentalTreatmentPlanLine(models.Model):
    _name = 'dental.treatment.plan.line'
    _description = 'Treatment Plan Line'

    plan_id = fields.Many2one('dental.treatment.plan', string='Treatment Plan', required=True, ondelete='cascade')
    treatment_id = fields.Many2one('product.template', string='Treatment', domain=[('is_dental_treatment', '=', True)], required=True)
    tooth_reference = fields.Char(string='Tooth Reference')
    description = fields.Text(string='Description')
    
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Float(string='Unit Price')
    discount = fields.Float(string='Discount (%)')
    estimated_amount = fields.Monetary(string='Estimated Amount', compute='_compute_amount', store=True)
    currency_id = fields.Many2one(related='plan_id.currency_id', depends=['plan_id.currency_id'], store=True)
    
    number_of_visits = fields.Integer(string='Number of Visits', default=1)
    notes = fields.Text(string='Notes')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    session_ids = fields.One2many('dental.treatment.session', 'plan_line_id', string='Sessions')

    @api.depends('quantity', 'unit_price', 'discount')
    def _compute_amount(self):
        for line in self:
            price = line.quantity * line.unit_price
            discount_amount = price * (line.discount / 100.0)
            line.estimated_amount = price - discount_amount

    @api.onchange('treatment_id')
    def _onchange_treatment_id(self):
        if self.treatment_id:
            self.description = self.treatment_id.name
            self.unit_price = self.treatment_id.list_price

class DentalTreatmentSession(models.Model):
    _name = 'dental.treatment.session'
    _description = 'Treatment Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Session Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    case_id = fields.Many2one('dental.case', string='Dental Case', tracking=True)
    plan_id = fields.Many2one('dental.treatment.plan', string='Treatment Plan', tracking=True)
    plan_line_id = fields.Many2one('dental.treatment.plan.line', string='Treatment Plan Line', required=True, tracking=True)
    
    doctor_id = fields.Many2one('hr.employee', string='Doctor', tracking=True)
    appointment_id = fields.Many2one('dental.appointment', string='Appointment', tracking=True)
    
    session_date = fields.Datetime(string='Session Date', default=fields.Datetime.now, required=True, tracking=True)
    tooth_reference = fields.Char(string='Tooth Reference')
    
    procedure_notes = fields.Text(string='Procedure Notes')
    clinical_notes = fields.Text(string='Clinical Notes')
    
    state = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='planned', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.treatment.session') or _('New')
        return super().create(vals_list)

    @api.onchange('plan_line_id')
    def _onchange_plan_line_id(self):
        if self.plan_line_id:
            self.tooth_reference = self.plan_line_id.tooth_reference
            if self.plan_line_id.plan_id:
                self.plan_id = self.plan_line_id.plan_id
                self.patient_id = self.plan_line_id.plan_id.patient_id
                self.case_id = self.plan_line_id.plan_id.case_id
