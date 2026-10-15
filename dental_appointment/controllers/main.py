# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
import logging
from odoo import http, fields, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class DentalAppointmentWebsiteController(http.Controller):

    @http.route(['/book-appointment', '/appointment'], type='http', auth='public', website=True, sitemap=True)
    def book_appointment_page(self, **kwargs):
        """Render the 6-step modern animated dental booking page."""
        dentists = request.env['hr.employee'].sudo().search([
            ('is_dentist', '=', True),
            ('active', '=', True),
        ], order='id asc')
        if not dentists:
            dentists = request.env['hr.employee'].sudo().search([
                ('id', 'in', [1, 4])
            ], order='id asc')

        appointment_types = request.env['dental.appointment.type'].sudo().search([
            ('active', '=', True),
        ], order='id asc')

        treatments = request.env['product.template'].sudo().search([
            ('is_dental_treatment', '=', True),
        ], order='sequence asc, name asc')

        branches = request.env['res.company'].sudo().search([])

        values = {
            'dentists': dentists,
            'appointment_types': appointment_types,
            'treatments': treatments,
            'branches': branches,
            'default_branch': request.env.company,
        }
        return request.render('dental_appointment.book_appointment', values)

    @http.route('/dental/check_patient', type='json', auth='public', methods=['POST'], csrf=False)
    def check_patient(self, identifier=None, **kwargs):
        """Search for an existing patient by phone number, email, or patient ID."""
        if not identifier:
            return {'found': False, 'message': _('Please enter a mobile phone number, email, or Patient ID.')}

        clean_id = str(identifier).strip()
        partner_obj = request.env['res.partner'].sudo()

        domain = [
            ('is_dental_patient', '=', True),
            '|', '|',
            ('phone', '=', clean_id),
            ('email', '=ilike', clean_id),
            ('dental_patient_id', '=ilike', clean_id),
        ]
        patient = partner_obj.search(domain, limit=1)

        clean_digits = ''.join([c for c in clean_id if c.isdigit()])
        if not patient and clean_digits and len(clean_digits) >= 7:
            patient = partner_obj.search([
                ('is_dental_patient', '=', True),
                ('phone', 'ilike', clean_digits),
            ], limit=1)

        if patient:
            return {
                'found': True,
                'patient': {
                    'id': patient.id,
                    'name': patient.name,
                    'phone': patient.phone or '',
                    'email': patient.email or '',
                    'dental_patient_id': patient.dental_patient_id or ('PT-%05d' % patient.id),
                    'gender': patient.gender or '',
                    'date_of_birth': str(patient.date_of_birth) if patient.date_of_birth else '',
                }
            }
        else:
            return {
                'found': False,
                'message': _('No patient record found matching "%s". You can easily register as a New Patient.') % clean_id
            }

    @http.route('/dental/get_slots', type='json', auth='public', methods=['POST'], csrf=False)
    def get_available_slots(self, date=None, doctor_id=None, duration=30, **kwargs):
        """Return available time slots for a given date, doctor, and duration."""
        target_date_str = date or fields.Date.context_today(request.env.user).strftime('%Y-%m-%d')
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except Exception:
            target_date = date.today()
            target_date_str = target_date.strftime('%Y-%m-%d')

        duration_val = float(duration or 30.0)
        now = datetime.now()
        is_today = (target_date == now.date())

        weekday = target_date.weekday()
        if weekday == 6: # Sunday
            raw_slots = [
                ('10:00', '10:00 AM', 'morning'),
                ('10:30', '10:30 AM', 'morning'),
                ('11:00', '11:00 AM', 'morning'),
                ('11:30', '11:30 AM', 'morning'),
                ('12:00', '12:00 PM', 'morning'),
                ('12:30', '12:30 PM', 'morning'),
                ('13:00', '01:00 PM', 'afternoon'),
                ('13:30', '01:30 PM', 'afternoon'),
            ]
        else:
            raw_slots = [
                ('09:00', '09:00 AM', 'morning'),
                ('09:30', '09:30 AM', 'morning'),
                ('10:00', '10:00 AM', 'morning'),
                ('10:30', '10:30 AM', 'morning'),
                ('11:00', '11:00 AM', 'morning'),
                ('11:30', '11:30 AM', 'morning'),
                ('12:00', '12:00 PM', 'morning'),
                ('12:30', '12:30 PM', 'morning'),
                ('14:00', '02:00 PM', 'afternoon'),
                ('14:30', '02:30 PM', 'afternoon'),
                ('15:00', '03:00 PM', 'afternoon'),
                ('15:30', '03:30 PM', 'afternoon'),
                ('16:00', '04:00 PM', 'afternoon'),
                ('16:30', '04:30 PM', 'afternoon'),
                ('17:00', '05:00 PM', 'afternoon'),
                ('17:30', '05:30 PM', 'afternoon'),
            ]

        emp_obj = request.env['hr.employee'].sudo()
        all_dentists = emp_obj.search([('is_dentist', '=', True), ('active', '=', True)], order='id asc')
        if not all_dentists:
            all_dentists = emp_obj.search([('id', 'in', [1, 4])], order='id asc')

        selected_doc = None
        if doctor_id and str(doctor_id).strip() not in ('', '0', 'any'):
            try:
                selected_doc = emp_obj.browse(int(doctor_id))
                if not selected_doc.exists():
                    selected_doc = None
            except Exception:
                selected_doc = None

        candidate_docs = [selected_doc] if selected_doc else all_dentists
        appt_obj = request.env['dental.appointment'].sudo()
        leave_obj = request.env['hr.leave'].sudo()

        slots_result = []
        for slot_time, label, period in raw_slots:
            slot_dt_start = datetime.strptime(f"{target_date_str} {slot_time}:00", '%Y-%m-%d %H:%M:%S')
            slot_dt_end = slot_dt_start + timedelta(minutes=duration_val)

            if is_today and slot_dt_start <= (now + timedelta(minutes=15)):
                slots_result.append({
                    'time': slot_time,
                    'label': label,
                    'period': period,
                    'available': False,
                    'reason': 'Past Time'
                })
                continue

            free_docs = []
            for doc in candidate_docs:
                overlap = appt_obj.search_count([
                    ('doctor_id', '=', doc.id),
                    ('state', 'not in', ['cancelled', 'no_show']),
                    ('date_start', '<', slot_dt_end),
                    ('date_end', '>', slot_dt_start),
                ])
                if overlap > 0:
                    continue

                leaves = leave_obj.search_count([
                    ('employee_id', '=', doc.id),
                    ('state', '=', 'validate'),
                    ('date_from', '<', slot_dt_end),
                    ('date_to', '>', slot_dt_start),
                ])
                if leaves > 0:
                    continue

                free_docs.append(doc.id)

            is_avail = len(free_docs) > 0
            slots_result.append({
                'time': slot_time,
                'label': label,
                'period': period,
                'available': is_avail,
                'reason': '' if is_avail else ('Doctor Booked' if selected_doc else 'Fully Booked'),
                'available_doctors': free_docs
            })

        return {
            'success': True,
            'date': target_date_str,
            'weekday': target_date.strftime('%A'),
            'slots': slots_result,
        }

    @http.route('/dental/book_appointment', type='json', auth='public', methods=['POST'], csrf=False)
    def book_appointment_submit(self, **post):
        """Handle appointment creation with real server availability validation."""
        patient_type = post.get('patient_type', 'new')
        doctor_id = post.get('doctor_id')
        appointment_type_id = post.get('appointment_type_id')
        treatment_id = post.get('treatment_id')
        branch_id = post.get('branch_id')
        appointment_date = post.get('appointment_date')
        appointment_time = post.get('appointment_time')
        notes = (post.get('notes') or post.get('reason') or '').strip()

        if not appointment_date or not appointment_time:
            return {'success': False, 'error': _('Please select an appointment date and time.')}

        # Resolve Appointment Type & Duration
        appt_type = None
        duration = 30.0
        if appointment_type_id:
            try:
                appt_type = request.env['dental.appointment.type'].sudo().browse(int(appointment_type_id))
                if appt_type.exists():
                    duration = float(appt_type.duration or 30.0)
            except Exception:
                appt_type = None

        try:
            dt_str = f"{appointment_date} {appointment_time}:00"
            date_start = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            date_end = date_start + timedelta(minutes=duration)
        except Exception as e:
            _logger.error("Failed to parse appointment datetime: %s", e)
            return {'success': False, 'error': _('Invalid date or time format.')}

        if date_start < datetime.now():
            return {'success': False, 'error': _('Cannot book an appointment in the past. Please select an upcoming slot.')}

        # Resolve Doctor & Validate Availability
        emp_obj = request.env['hr.employee'].sudo()
        doctor = None
        if doctor_id and str(doctor_id).strip() not in ('', '0', 'any'):
            try:
                doctor = emp_obj.browse(int(doctor_id))
                if not doctor.exists():
                    doctor = None
            except Exception:
                doctor = None

        appt_obj = request.env['dental.appointment'].sudo()
        leave_obj = request.env['hr.leave'].sudo()

        if doctor:
            overlap = appt_obj.search_count([
                ('doctor_id', '=', doctor.id),
                ('state', 'not in', ['cancelled', 'no_show']),
                ('date_start', '<', date_end),
                ('date_end', '>', date_start),
            ])
            if overlap > 0:
                return {
                    'success': False,
                    'error': _('Doctor %s is already booked for this time slot (%s - %s). Please pick another time or choose Any Specialist.') % (
                        doctor.name, appointment_time, date_end.strftime('%H:%M')
                    )
                }

            leaves = leave_obj.search_count([
                ('employee_id', '=', doctor.id),
                ('state', '=', 'validate'),
                ('date_from', '<', date_end),
                ('date_to', '>', date_start),
            ])
            if leaves > 0:
                return {
                    'success': False,
                    'error': _('Doctor %s is on scheduled leave during this time. Please pick another time.') % doctor.name
                }
        else:
            all_dentists = emp_obj.search([('is_dentist', '=', True), ('active', '=', True)], order='id asc')
            if not all_dentists:
                all_dentists = emp_obj.search([('id', 'in', [1, 4])], order='id asc')

            for d in all_dentists:
                overlap = appt_obj.search_count([
                    ('doctor_id', '=', d.id),
                    ('state', 'not in', ['cancelled', 'no_show']),
                    ('date_start', '<', date_end),
                    ('date_end', '>', date_start),
                ])
                if overlap == 0:
                    leaves = leave_obj.search_count([
                        ('employee_id', '=', d.id),
                        ('state', '=', 'validate'),
                        ('date_from', '<', date_end),
                        ('date_to', '>', date_start),
                    ])
                    if leaves == 0:
                        doctor = d
                        break

            if not doctor:
                return {
                    'success': False,
                    'error': _('All dental specialists are fully booked for this time slot. Please choose another date or time.')
                }

        # Resolve Patient
        partner_obj = request.env['res.partner'].sudo()
        patient = None

        if patient_type == 'returning':
            existing_id = post.get('patient_id')
            if not existing_id:
                return {'success': False, 'error': _('Patient record not specified.')}
            patient = partner_obj.browse(int(existing_id))
            if not patient.exists():
                return {'success': False, 'error': _('Selected patient record does not exist.')}
        else:
            name = (post.get('name') or '').strip()
            phone = (post.get('phone') or '').strip()
            email = (post.get('email') or '').strip()
            dob = post.get('dob') or False
            gender = post.get('gender') or False

            if not name:
                return {'success': False, 'error': _('Please enter your full name.')}
            if not phone:
                return {'success': False, 'error': _('Please enter your phone number.')}

            clean_digits = ''.join([c for c in phone if c.isdigit()])
            existing = partner_obj.search([
                ('is_dental_patient', '=', True),
                ('phone', '=', phone),
            ], limit=1)
            if not existing and clean_digits and len(clean_digits) >= 7:
                existing = partner_obj.search([
                    ('is_dental_patient', '=', True),
                    ('phone', 'ilike', clean_digits),
                ], limit=1)

            if existing:
                patient = existing
                updates = {}
                if email and not patient.email:
                    updates['email'] = email
                if dob and not patient.date_of_birth:
                    updates['date_of_birth'] = dob
                if gender and not patient.gender:
                    updates['gender'] = gender
                if updates:
                    patient.write(updates)
            else:
                patient = partner_obj.create({
                    'name': name,
                    'phone': phone,
                    'email': email or False,
                    'date_of_birth': dob or False,
                    'gender': gender or False,
                    'is_dental_patient': True,
                    'customer_rank': 1,
                })

        # Resolve Company/Branch
        branch = None
        if branch_id:
            try:
                branch = request.env['res.company'].sudo().browse(int(branch_id))
            except Exception:
                branch = request.env.company
        else:
            branch = request.env.company

        # Resolve Treatment
        treatment = None
        if treatment_id:
            try:
                treatment = request.env['product.template'].sudo().browse(int(treatment_id))
                if not treatment.exists():
                    treatment = None
            except Exception:
                treatment = None
        if not treatment:
            treatment = request.env['product.template'].sudo().search([('is_dental_treatment', '=', True)], limit=1)

        service_title = appt_type.name if appt_type else (treatment.name if treatment else 'Dental Appointment')
        reason_text = service_title
        if notes:
            reason_text = f"{service_title} - {notes}"

        # Create Appointment Record
        try:
            appt_vals = {
                'patient_id': patient.id,
                'doctor_id': doctor.id,
                'appointment_type_id': appt_type.id if appt_type else False,
                'treatment_id': treatment.id if treatment else False,
                'branch_id': branch.id if branch else False,
                'date_start': date_start,
                'date_end': date_end,
                'reason': reason_text,
                'notes': notes,
                'state': 'pending',
                'priority': '1',
            }
            appointment = request.env['dental.appointment'].sudo().create(appt_vals)

            try:
                template = request.env.ref('dental_appointment.email_template_appointment_confirmation', raise_if_not_found=False)
                if template and patient.email:
                    template.sudo().send_mail(appointment.id, force_send=False)
            except Exception as mail_err:
                _logger.info("Email confirmation skipped: %s", mail_err)

            return {
                'success': True,
                'appointment_id': appointment.id,
                'appointment_name': appointment.name,
                'patient_name': patient.name,
                'patient_id': patient.dental_patient_id or ('PT-%05d' % patient.id),
                'doctor_name': doctor.name,
                'doctor_specialization': doctor.specialization or 'Dental Specialist',
                'service_name': service_title,
                'duration_min': int(duration),
                'date_str': appointment_date,
                'date_formatted': date_start.strftime('%A, %B %d, %Y'),
                'time_str': appointment_time,
                'time_formatted': date_start.strftime('%I:%M %p'),
                'status': 'Pending Confirmation',
            }
        except Exception as e:
            _logger.exception("Error booking dental appointment: %s", e)
            return {'success': False, 'error': str(e)}
