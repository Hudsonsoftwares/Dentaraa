from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class DentalAppointment(models.Model):
    _name = 'dental.appointment'
    _description = 'Dental Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Appointment Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    doctor_id = fields.Many2one('hr.employee.public', string='Doctor', required=True, domain=[('is_dentist', '=', True)], tracking=True)
    treatment_id = fields.Many2one('product.template', string='Dental Treatment', domain=[('is_dental_treatment', '=', True)], tracking=True)
    appointment_type_id = fields.Many2one('dental.appointment.type', string='Appointment Type', tracking=True)
    
    date_start = fields.Datetime(string='Start Time', required=True, tracking=True)
    date_end = fields.Datetime(string='End Time', required=True, tracking=True)
    duration = fields.Float(string='Duration', compute='_compute_duration', store=True)
    
    reason = fields.Text(string='Reason / Chief Complaint')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')
    notes = fields.Html(string='Notes')
    
    branch_id = fields.Many2one('res.company', string='Branch', default=lambda self: self.env.company)
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_consultation', 'In Consultation'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show')
    ], string='Status', default='pending', tracking=True, copy=False)
    
    calendar_event_id = fields.Many2one('calendar.event', string='Calendar Event', copy=False, ondelete='set null')
    
    is_emergency = fields.Boolean(string='Emergency', default=False, tracking=True)
    token_number = fields.Char(string='Token Number', readonly=True, copy=False)
    queue_priority = fields.Integer(string='Queue Priority', compute='_compute_queue_priority', store=True)
    
    check_in_time = fields.Datetime(string='Check-in Time', readonly=True, copy=False)
    called_time = fields.Datetime(string='Called Time', readonly=True, copy=False)
    waiting_time = fields.Float(string='Waiting Time (Minutes)', compute='_compute_waiting_time')
    
    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for record in self:
            if record.date_start and record.date_end:
                diff = record.date_end - record.date_start
                record.duration = diff.total_seconds() / 3600.0
            else:
                record.duration = 0.0

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start and not self.date_end:
            self.date_end = self.date_start + timedelta(minutes=30)
            
    @api.depends('is_emergency', 'check_in_time')
    def _compute_queue_priority(self):
        for record in self:
            if record.is_emergency:
                record.queue_priority = 10
            else:
                record.queue_priority = 5
                
    @api.depends('check_in_time', 'called_time', 'state')
    def _compute_waiting_time(self):
        for record in self:
            if record.check_in_time:
                end_time = record.called_time or fields.Datetime.now()
                diff = end_time - record.check_in_time
                record.waiting_time = diff.total_seconds() / 60.0
            else:
                record.waiting_time = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.appointment') or _('New')
        appointments = super().create(vals_list)
        appointments._sync_calendar_event()
        return appointments

    def write(self, vals):
        res = super().write(vals)
        if set(vals.keys()) & {'date_start', 'date_end', 'state', 'patient_id', 'doctor_id', 'treatment_id', 'appointment_type_id'}:
            self._sync_calendar_event()
        return res

    def _sync_calendar_event(self):
        for app in self:
            if app.state in ['cancelled', 'no_show'] and app.calendar_event_id:
                app.calendar_event_id.unlink()
            elif app.state not in ['cancelled', 'no_show'] and app.date_start and app.date_end:
                title = f"Dental: {app.patient_id.name}"
                if app.treatment_id:
                    title += f" - {app.treatment_id.name}"
                elif app.appointment_type_id:
                    title += f" - {app.appointment_type_id.name}"
                    
                vals = {
                    'name': title,
                    'start': app.date_start,
                    'stop': app.date_end,
                    'description': app.reason,
                    'res_model_id': self.env.ref('dental_appointment.model_dental_appointment').id,
                    'res_id': app.id,
                }
                partners = [app.patient_id.id]
                if app.doctor_id.user_id and app.doctor_id.user_id.partner_id:
                    partners.append(app.doctor_id.user_id.partner_id.id)
                vals['partner_ids'] = [(6, 0, partners)]
                
                if app.calendar_event_id:
                    app.calendar_event_id.sudo().write(vals)
                else:
                    event = self.env['calendar.event'].sudo().create(vals)
                    app.calendar_event_id = event.id

    @api.constrains('doctor_id', 'date_start', 'date_end', 'state')
    def _check_doctor_availability(self):
        for record in self:
            if record.state in ['cancelled', 'no_show']:
                continue
            if not record.doctor_id or not record.date_start or not record.date_end:
                continue
                
            # Check overlap
            domain = [
                ('id', '!=', record.id),
                ('doctor_id', '=', record.doctor_id.id),
                ('state', 'not in', ['cancelled', 'no_show']),
                ('date_start', '<', record.date_end),
                ('date_end', '>', record.date_start)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_("Doctor %s already has an appointment during this time.") % record.doctor_id.name)
                
            # Check leave
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', record.doctor_id.id),
                ('state', '=', 'validate'),
                ('date_from', '<', record.date_end),
                ('date_to', '>', record.date_start)
            ])
            if leaves:
                raise ValidationError(_("Doctor %s is on leave during this time.") % record.doctor_id.name)

    def action_confirm(self):
        for record in self:
            if record.state == 'confirmed':
                continue
            record.state = 'confirmed'
            
            # Send confirmation email
            if not record.patient_id.email:
                record.message_post(body=_('Warning: Could not send confirmation email. Patient has no email address configured.'))
            else:
                template = self.env.ref('dental_appointment.email_template_appointment_confirmation', raise_if_not_found=False)
                if template:
                    template.send_mail(record.id, force_send=False)
                    record.message_post(body=_('Appointment confirmation email queued for sending to %s.') % record.patient_id.email)

    def action_check_in(self):
        for record in self:
            if record.state in ['checked_in', 'in_consultation', 'completed', 'cancelled']:
                continue
                
            if not record.token_number:
                branch_code = 'APT'
                if hasattr(record.branch_id, 'name') and record.branch_id.name:
                    branch_code = ''.join(e for e in record.branch_id.name if e.isalnum())[:3].upper()
                    if not branch_code:
                        branch_code = 'APT'
                
                date_str = fields.Date.context_today(record).strftime('%Y%m%d')
                seq = self.env['ir.sequence'].next_by_code('dental.queue.token') or '001'
                record.token_number = f"{branch_code}-{date_str}-{seq}"
                
            record.write({
                'state': 'checked_in',
                'check_in_time': fields.Datetime.now()
            })

    def action_start_consultation(self):
        for record in self:
            record.write({
                'state': 'in_consultation',
                'called_time': fields.Datetime.now()
            })

    def action_complete(self):
        for record in self:
            record.state = 'completed'
            
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
            
    def action_no_show(self):
        for record in self:
            record.state = 'no_show'
            
    def action_reschedule(self):
        for record in self:
            record.state = 'pending'
