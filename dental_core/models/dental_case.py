from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class DentalCase(models.Model):
    _name = 'dental.case'
    _description = 'Dental Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Case Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], tracking=True)
    doctor_id = fields.Many2one('hr.employee.public', string='Doctor', tracking=True)
    appointment_id = fields.Many2one('dental.appointment', string='Related Appointment', tracking=True)
    branch_id = fields.Many2one('res.company', string='Branch', related='appointment_id.branch_id', store=True)
    
    case_date = fields.Date(string='Case Date', default=fields.Date.context_today, required=True, tracking=True)
    
    chief_complaint = fields.Text(string='Chief Complaint')
    clinical_notes = fields.Text(string='Clinical Notes')
    
    medical_history_summary = fields.Text(string='Medical History Summary')
    dental_history_summary = fields.Text(string='Dental History Summary')
    allergies = fields.Text(string='Allergies')
    current_medications = fields.Text(string='Current Medications')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('under_treatment', 'Under Treatment'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Case Status', default='draft', tracking=True)
    
    examination_ids = fields.One2many('dental.clinical.examination', 'case_id', string='Examinations')
    tooth_finding_ids = fields.One2many('dental.tooth.finding', 'case_id', string='Tooth Findings')
    odontogram_chart = fields.Text(string='Odontogram Chart', default='{}')
    diagnosis_ids = fields.One2many('dental.patient.diagnosis', 'case_id', string='Diagnoses')
    treatment_plan_ids = fields.One2many('dental.treatment.plan', 'case_id', string='Treatment Plans')
    treatment_session_ids = fields.One2many('dental.treatment.session', 'case_id', string='Treatment Sessions')
    completion_time = fields.Datetime(string='Completion Time', readonly=True)

    def action_complete_consultation(self):
        for record in self:
            if not record.chief_complaint:
                raise ValidationError(_("Chief Complaint is required to complete the consultation."))
            
            # Record completion time
            if not record.completion_time:
                record.completion_time = fields.Datetime.now()
            
            # Update case state if draft
            if record.state == 'draft':
                record.state = 'open'
                
            # Update appointment state
            if record.appointment_id and record.appointment_id.state in ['checked_in', 'in_consultation']:
                record.appointment_id.action_complete()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.case') or _('New')
        return super().create(vals_list)

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            self.medical_history_summary = self.patient_id.existing_conditions
            self.allergies = self.patient_id.allergies
            self.current_medications = self.patient_id.current_medications
            self.dental_history_summary = self.patient_id.previous_dental_treatments

    def get_odontogram_data(self, patient_id=None):
        case = self and self[0] or None
        target_patient_id = patient_id or (case and case.patient_id.id)
        if not target_patient_id:
            return {
                'case_id': case.id if case else False,
                'patient_id': False,
                'patient_name': '',
                'doctor_id': case.doctor_id.id if case and case.doctor_id else False,
                'doctor_name': case.doctor_id.name if case and case.doctor_id else '',
                'teeth': {},
                'stats': {'sound': 32, 'caries': 0, 'restoration': 0, 'missing': 0, 'crown': 0, 'root_canal': 0, 'implant': 0, 'other': 0, 'total_teeth': 32},
                'can_edit': self.env.user.has_group('dental_base.group_dental_dentist') or self.env.user.has_group('dental_base.group_dental_manager') or self.env.user.has_group('dental_base.group_dental_admin'),
                'is_dentist': self.env.user.has_group('dental_base.group_dental_dentist') or self.env.user.has_group('dental_base.group_dental_manager') or self.env.user.has_group('dental_base.group_dental_admin')
            }

        patient = self.env['res.partner'].browse(target_patient_id)
        
        # Calculate patient age
        patient_age = patient.age if hasattr(patient, 'age') else 0
        if not patient_age and hasattr(patient, 'date_of_birth') and patient.date_of_birth:
            from datetime import date
            from dateutil.relativedelta import relativedelta
            patient_age = relativedelta(date.today(), patient.date_of_birth).years

        # Suggested dentition based on age:
        # 0-5: primary
        # 6-12: mixed
        # 13+: permanent
        if patient_age <= 5:
            suggested_dentition = 'primary'
        elif 6 <= patient_age <= 12:
            suggested_dentition = 'mixed'
        else:
            suggested_dentition = 'permanent'

        findings = self.env['dental.tooth.finding'].search([
            ('patient_id', '=', target_patient_id),
            ('active', '=', True)
        ], order='finding_date desc, id desc')

        from .dental_tooth_finding import TOOTH_NAMES
        teeth = {}
        # Prepopulate 32 adult permanent teeth
        for quad in [1, 2, 3, 4]:
            for pos in range(1, 9):
                t_num = f"{quad}{pos}"
                teeth[t_num] = {
                    'tooth_number': t_num,
                    'is_primary': False,
                    'condition': 'sound',
                    'surfaces': '',
                    'severity': '',
                    'treatment_indicated': '',
                    'notes': '',
                    'latest_date': '',
                    'findings_count': 0,
                    'history': [],
                    'diagnoses': [],
                    'proposed_treatments': [],
                    'completed_treatments': [],
                    'sessions': []
                }
        # Prepopulate 20 primary deciduous teeth
        for quad in [5, 6, 7, 8]:
            for pos in range(1, 6):
                t_num = f"{quad}{pos}"
                teeth[t_num] = {
                    'tooth_number': t_num,
                    'is_primary': True,
                    'condition': 'sound',
                    'surfaces': '',
                    'severity': '',
                    'treatment_indicated': '',
                    'notes': '',
                    'latest_date': '',
                    'findings_count': 0,
                    'history': [],
                    'diagnoses': [],
                    'proposed_treatments': [],
                    'completed_treatments': [],
                    'sessions': []
                }

        for f in findings:
            t_num = str(f.tooth_number).strip()
            if t_num not in teeth:
                teeth[t_num] = {
                    'tooth_number': t_num,
                    'condition': 'sound',
                    'surfaces': '',
                    'severity': '',
                    'treatment_indicated': '',
                    'notes': '',
                    'latest_date': '',
                    'findings_count': 0,
                    'history': [],
                    'diagnoses': [],
                    'proposed_treatments': [],
                    'completed_treatments': [],
                    'sessions': []
                }
            entry = teeth[t_num]
            entry['findings_count'] += 1
            if len(entry['history']) == 0:
                entry['condition'] = f.condition
                entry['surfaces'] = f.surfaces or ''
                entry['severity'] = f.severity or ''
                entry['treatment_indicated'] = f.treatment_indicated or ''
                entry['notes'] = f.notes or ''
                entry['latest_date'] = f.finding_date.strftime('%d %b %Y %H:%M') if f.finding_date else ''
                entry['latest_case_name'] = f.case_id.name if f.case_id else ''

            entry['history'].append({
                'id': f.id,
                'name': f.name,
                'date': f.finding_date.strftime('%d %b %Y %H:%M') if f.finding_date else '',
                'condition': f.condition,
                'condition_label': dict(f._fields['condition'].selection).get(f.condition, f.condition),
                'surfaces': f.surfaces or '',
                'severity': f.severity or '',
                'severity_label': dict(f._fields['severity'].selection).get(f.severity, f.severity) if f.severity else '',
                'diagnosis_id': f.diagnosis_id.id if hasattr(f, 'diagnosis_id') and f.diagnosis_id else False,
                'diagnosis_name': f.diagnosis_id.name if hasattr(f, 'diagnosis_id') and f.diagnosis_id else '',
                'treatment_indicated': f.treatment_indicated or '',
                'notes': f.notes or '',
                'case_id': f.case_id.id if f.case_id else False,
                'case_name': f.case_id.name if f.case_id else _('Historical Visit'),
                'doctor_name': f.doctor_id.name if f.doctor_id else '',
                'is_current_case': bool(case and f.case_id.id == case.id)
            })

            if hasattr(f, 'diagnosis_id') and f.diagnosis_id:
                entry['diagnoses'].append({
                    'id': f.id,
                    'diagnosis_id': f.diagnosis_id.id,
                    'diagnosis_name': f.diagnosis_id.name,
                    'diagnosis_code': f.diagnosis_id.code or '',
                    'date': f.finding_date.strftime('%d %b %Y') if f.finding_date else '',
                    'status': 'confirmed',
                    'status_label': _('Confirmed Finding'),
                    'doctor_name': f.doctor_id.name if f.doctor_id else '',
                    'notes': f.notes or '',
                    'case_name': f.case_id.name if f.case_id else '',
                })

        for t_num, entry in teeth.items():
            info = TOOTH_NAMES.get(t_num)
            if info:
                entry['tooth_name'] = info[0]
                entry['universal_number'] = info[1]
                entry['palmer_notation'] = info[2]
            else:
                entry['tooth_name'] = f"Tooth {t_num}"
                entry['universal_number'] = t_num
                entry['palmer_notation'] = t_num

        patient_diags = self.env['dental.patient.diagnosis'].search([
            ('patient_id', '=', target_patient_id)
        ], order='date desc, id desc')
        for pd in patient_diags:
            ref = str(getattr(pd, 'tooth_reference', '') or '').strip()
            pd_item = {
                'id': pd.id,
                'diagnosis_id': pd.diagnosis_id.id,
                'diagnosis_name': pd.diagnosis_id.name,
                'diagnosis_code': pd.diagnosis_id.code or '',
                'date': pd.date.strftime('%d %b %Y') if pd.date else '',
                'status': pd.status,
                'status_label': dict(pd._fields['status'].selection).get(pd.status, pd.status),
                'doctor_name': pd.doctor_id.name if pd.doctor_id else '',
                'notes': pd.notes or '',
                'case_id': pd.case_id.id if pd.case_id else False,
                'case_name': pd.case_id.name if pd.case_id else '',
            }
            if ref:
                parts = [x.strip() for x in ref.replace(';', ',').split(',') if x.strip()]
                for t_num in teeth:
                    if t_num in parts:
                        teeth[t_num]['diagnoses'].append(pd_item)

        plan_lines = self.env['dental.treatment.plan.line'].search([
            ('plan_id.patient_id', '=', target_patient_id)
        ])
        for line in plan_lines:
            ref = str(line.tooth_reference or '').strip()
            if ref:
                parts = [x.strip() for x in ref.replace(';', ',').split(',') if x.strip()]
                for t_num in teeth:
                    if t_num in parts or ref == t_num:
                        item = {
                            'id': line.id,
                            'plan_id': line.plan_id.id,
                            'plan_name': line.plan_id.name,
                            'treatment_name': line.treatment_id.name if line.treatment_id else _('Dental Procedure'),
                            'description': line.description or '',
                            'state': line.state,
                            'state_label': dict(line._fields['state'].selection).get(line.state, line.state),
                            'estimated_amount': line.estimated_amount,
                            'is_completed': line.state == 'completed',
                        }
                        if line.state == 'completed':
                            teeth[t_num]['completed_treatments'].append(item)
                        else:
                            teeth[t_num]['proposed_treatments'].append(item)

        sessions = self.env['dental.treatment.session'].search([
            ('patient_id', '=', target_patient_id)
        ], order='session_date desc, id desc')
        for sess in sessions:
            ref = str(sess.tooth_reference or '').strip()
            if ref:
                parts = [x.strip() for x in ref.replace(';', ',').split(',') if x.strip()]
                for t_num in teeth:
                    if t_num in parts or ref == t_num:
                        t_name = sess.plan_line_id.treatment_id.name if sess.plan_line_id and sess.plan_line_id.treatment_id else sess.name
                        item = {
                            'id': sess.id,
                            'name': sess.name,
                            'treatment_name': t_name,
                            'date': sess.session_date.strftime('%d %b %Y') if sess.session_date else '',
                            'state': sess.state,
                            'state_label': dict(sess._fields['state'].selection).get(sess.state, sess.state),
                            'doctor_name': sess.doctor_id.name if sess.doctor_id else '',
                            'procedure_notes': sess.procedure_notes or '',
                            'is_completed': sess.state == 'completed',
                        }
                        teeth[t_num]['sessions'].append(item)
                        if sess.state == 'completed':
                            teeth[t_num]['completed_treatments'].append(item)

        stats = {
            'sound': 0,
            'caries': 0,
            'restoration': 0,
            'missing': 0,
            'crown': 0,
            'root_canal': 0,
            'implant': 0,
            'other': 0,
            'total_teeth': 32
        }
        for q in [1, 2, 3, 4]:
            for p in range(1, 9):
                tn = f"{q}{p}"
                cond = teeth.get(tn, {}).get('condition', 'sound')
                if cond in stats:
                    stats[cond] += 1
                elif cond == 'sound':
                    stats['sound'] += 1
                else:
                    stats['other'] += 1

        is_dentist = (
            self.env.user.has_group('dental_base.group_dental_dentist') or 
            self.env.user.has_group('dental_base.group_dental_manager') or
            self.env.user.has_group('dental_base.group_dental_admin')
        )

        diagnosis_masters = self.env['dental.diagnosis'].search_read(
            [('active', '=', True)],
            ['id', 'name', 'code', 'description'],
            order='name asc'
        )

        return {
            'case_id': case.id if case else False,
            'case_name': case.name if case else '',
            'case_state': case.state if case else '',
            'patient_id': patient.id,
            'patient_name': patient.name,
            'patient_ref': patient.ref or (getattr(patient, 'patient_id_number', False) or ''),
            'patient_dob': patient.date_of_birth.strftime('%d %b %Y') if hasattr(patient, 'date_of_birth') and patient.date_of_birth else '',
            'patient_age': patient_age,
            'suggested_dentition': suggested_dentition,
            'doctor_id': case.doctor_id.id if case and case.doctor_id else False,
            'doctor_name': case.doctor_id.name if case and case.doctor_id else '',
            'teeth': teeth,
            'stats': stats,
            'diagnosis_masters': diagnosis_masters,
            'can_edit': is_dentist and (case.state not in ['completed', 'cancelled'] if case else True),
            'is_dentist': is_dentist,
        }

    def save_tooth_finding(self, tooth_data):
        self.ensure_one()
        is_dentist = (
            self.env.user.has_group('dental_base.group_dental_dentist') or 
            self.env.user.has_group('dental_base.group_dental_manager') or
            self.env.user.has_group('dental_base.group_dental_admin')
        )
        if not is_dentist:
            raise UserError(_("Access Denied: Only authorized dentists and clinic managers can record tooth findings."))

        if self.state in ['completed', 'cancelled']:
            raise UserError(_("Tooth findings cannot be added to a completed or cancelled dental case."))

        tooth_number = str(tooth_data.get('tooth_number', '')).strip()
        if not tooth_number:
            raise ValidationError(_("Tooth number is required."))

        condition = tooth_data.get('condition', 'sound')
        surfaces = str(tooth_data.get('surfaces', '')).strip().upper()
        severity = tooth_data.get('severity', 'moderate')
        treatment_indicated = tooth_data.get('treatment_indicated', '')
        notes = tooth_data.get('notes', '')

        diagnosis_id = tooth_data.get('diagnosis_id')
        if diagnosis_id:
            try:
                diagnosis_id = int(diagnosis_id)
            except (ValueError, TypeError):
                diagnosis_id = False
        else:
            diagnosis_id = False

        doctor = self.doctor_id
        if not doctor and hasattr(self.env.user, 'employee_ids') and self.env.user.employee_ids:
            doctor = self.env.user.employee_ids[0]

        finding_vals = {
            'patient_id': self.patient_id.id,
            'case_id': self.id,
            'doctor_id': doctor.id if doctor else False,
            'tooth_number': tooth_number,
            'condition': condition,
            'surfaces': surfaces,
            'severity': severity,
            'treatment_indicated': treatment_indicated,
            'notes': notes,
            'finding_date': fields.Datetime.now(),
            'state': 'active',
        }
        if diagnosis_id:
            finding_vals['diagnosis_id'] = diagnosis_id

        finding = self.env['dental.tooth.finding'].create(finding_vals)

        if diagnosis_id:
            existing_diag = self.env['dental.patient.diagnosis'].search([
                ('patient_id', '=', self.patient_id.id),
                ('case_id', '=', self.id),
                ('diagnosis_id', '=', diagnosis_id),
                ('tooth_reference', '=', tooth_number)
            ], limit=1)
            if not existing_diag:
                self.env['dental.patient.diagnosis'].create({
                    'patient_id': self.patient_id.id,
                    'case_id': self.id,
                    'doctor_id': doctor.id if doctor else False,
                    'diagnosis_id': diagnosis_id,
                    'tooth_reference': tooth_number,
                    'notes': notes or _('Diagnosed during dental examination for Tooth %s', tooth_number),
                    'status': 'confirmed',
                })

        return {
            'success': True,
            'finding_id': finding.id,
            'finding_name': finding.name,
            'odontogram_data': self.get_odontogram_data()
        }

    def clear_tooth_finding(self, tooth_number):
        self.ensure_one()
        is_dentist = (
            self.env.user.has_group('dental_base.group_dental_dentist') or 
            self.env.user.has_group('dental_base.group_dental_manager') or
            self.env.user.has_group('dental_base.group_dental_admin')
        )
        if not is_dentist:
            raise UserError(_("Access Denied: Only authorized dentists and clinic managers can modify tooth findings."))

        if self.state in ['completed', 'cancelled']:
            raise UserError(_("Tooth findings cannot be modified in a completed or cancelled dental case."))

        t_num = str(tooth_number or '').strip()
        if not t_num:
            raise ValidationError(_("Tooth number is required."))

        # Create a new sound finding record to document the resolution/clear status
        doctor = self.doctor_id
        if not doctor and hasattr(self.env.user, 'employee_ids') and self.env.user.employee_ids:
            doctor = self.env.user.employee_ids[0]

        finding = self.env['dental.tooth.finding'].create({
            'patient_id': self.patient_id.id,
            'case_id': self.id,
            'doctor_id': doctor.id if doctor else False,
            'tooth_number': t_num,
            'condition': 'sound',
            'surfaces': '',
            'severity': 'mild',
            'notes': _('Cleared / Marked Sound during consultation'),
            'finding_date': fields.Datetime.now(),
            'state': 'active',
        })

        return {
            'success': True,
            'finding_id': finding.id,
            'odontogram_data': self.get_odontogram_data()
        }

