import psycopg2
import json

conn = psycopg2.connect(dbname='DenBell', user='odoo', password='odoopwd', host='localhost', port=5432)
cur = conn.cursor()

# -------------------------------------------------------------
# ACTION 980: check_patient
# -------------------------------------------------------------
check_patient_code = """
try:
    identifier = str(request.params.get('identifier') or '').strip()
    if not identifier:
        action = request.make_json_response({'found': False, 'message': 'Please enter a mobile number, email, or Patient ID.'})
    else:
        partner_obj = env['res.partner'].sudo()
        clean_digits = ''.join([c for c in identifier if c.isdigit()])
        domain = [
            ('is_dental_patient', '=', True),
            '|', '|',
            ('phone', '=', identifier),
            ('email', '=ilike', identifier),
            ('dental_patient_id', '=ilike', identifier),
        ]
        patient = partner_obj.search(domain, limit=1)
        if not patient and clean_digits and len(clean_digits) >= 7:
            patient = partner_obj.search([
                ('is_dental_patient', '=', True),
                ('phone', 'ilike', clean_digits),
            ], limit=1)
        if patient:
            action = request.make_json_response({
                'found': True,
                'patient': {
                    'id': patient.id,
                    'name': patient.name,
                    'phone': patient.phone or '',
                    'email': patient.email or '',
                    'dental_patient_id': patient.dental_patient_id or ('PT-%05d' % patient.id),
                    'gender': patient.gender or '',
                }
            })
        else:
            action = request.make_json_response({
                'found': False,
                'message': 'No patient record found matching "%s". You can quickly register as a New Patient.' % identifier
            })
except Exception as e:
    log('check_patient error: %s' % str(e), level='error')
    action = request.make_json_response({'found': False, 'message': str(e)})
"""

# -------------------------------------------------------------
# ACTION 982: get_slots
# -------------------------------------------------------------
get_slots_code = """
try:
    params = request.params
    target_date_str = params.get('date') or datetime.date.today().strftime('%Y-%m-%d')
    doctor_id = params.get('doctor_id')
    duration = float(params.get('duration') or 30.0)

    try:
        target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except Exception:
        target_date = datetime.date.today()
        target_date_str = target_date.strftime('%Y-%m-%d')

    now = datetime.datetime.now()
    is_today = (target_date == now.date())

    # Working hours definition
    # Mon-Sat: 09:00 - 13:00, 14:00 - 18:00
    # Sunday: 10:00 - 14:00
    weekday = target_date.weekday() # 0 = Monday, 6 = Sunday

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

    emp_obj = env['hr.employee'].sudo()
    all_dentists = emp_obj.search([('is_dentist', '=', True), ('active', '=', True)])
    if not all_dentists:
        all_dentists = emp_obj.search([('id', 'in', [1, 4])])

    selected_doc = None
    if doctor_id and str(doctor_id).strip() and str(doctor_id).strip() != '0' and str(doctor_id).strip() != 'any':
        try:
            selected_doc = emp_obj.browse(int(doctor_id))
            if not selected_doc.exists():
                selected_doc = None
        except Exception:
            selected_doc = None

    candidate_docs = [selected_doc] if selected_doc else all_dentists

    appt_obj = env['dental.appointment'].sudo()
    leave_obj = env['hr.leave'].sudo()

    slots_result = []

    for slot_time, label, period in raw_slots:
        slot_dt_start = datetime.datetime.strptime('%s %s:00' % (target_date_str, slot_time), '%Y-%m-%d %H:%M:%S')
        slot_dt_end = slot_dt_start + datetime.timedelta(minutes=duration)

        # 1. Past check
        if is_today and slot_dt_start <= (now + datetime.timedelta(minutes=15)):
            slots_result.append({
                'time': slot_time,
                'label': label,
                'period': period,
                'available': False,
                'reason': 'Past Time'
            })
            continue

        # 2. Check doctor availability
        free_docs = []
        for doc in candidate_docs:
            # Overlap check
            overlap = appt_obj.search_count([
                ('doctor_id', '=', doc.id),
                ('state', 'not in', ['cancelled', 'no_show']),
                ('date_start', '<', slot_dt_end),
                ('date_end', '>', slot_dt_start),
            ])
            if overlap > 0:
                continue

            # Leave check
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

    action = request.make_json_response({
        'success': True,
        'date': target_date_str,
        'weekday': target_date.strftime('%A'),
        'slots': slots_result
    })
except Exception as e:
    log('get_slots error: %s' % str(e), level='error')
    action = request.make_json_response({'success': False, 'error': str(e)})
"""

# -------------------------------------------------------------
# ACTION 981: book_appointment
# -------------------------------------------------------------
book_appointment_code = """
try:
    params = request.params
    patient_type = params.get('patient_type', 'new')
    name = (params.get('name') or '').strip()
    phone = (params.get('phone') or '').strip()
    email = (params.get('email') or '').strip()
    dob = params.get('dob') or False
    gender = params.get('gender') or False
    patient_id = params.get('patient_id')
    appointment_type_id = params.get('appointment_type_id')
    doctor_id = params.get('doctor_id')
    treatment_id = params.get('treatment_id')
    appointment_date = params.get('appointment_date')
    appointment_time = params.get('appointment_time')
    notes = (params.get('notes') or params.get('reason') or '').strip()

    if not appointment_date or not appointment_time:
        action = request.make_json_response({'success': False, 'error': 'Please select an appointment date and time.'})
    else:
        # Resolve Appointment Type & Duration
        appt_type = None
        duration = 30.0
        if appointment_type_id:
            try:
                appt_type = env['dental.appointment.type'].sudo().browse(int(appointment_type_id))
                if appt_type.exists():
                    duration = float(appt_type.duration or 30.0)
            except Exception:
                appt_type = None

        dt_start_str = '%s %s:00' % (appointment_date, appointment_time)
        dt_start = datetime.datetime.strptime(dt_start_str, '%Y-%m-%d %H:%M:%S')
        dt_end = dt_start + datetime.timedelta(minutes=duration)

        if dt_start < datetime.datetime.now():
            action = request.make_json_response({'success': False, 'error': 'Cannot book an appointment in the past. Please select an upcoming date and time.'})
        else:
            # Resolve Doctor & Validate Availability
            emp_obj = env['hr.employee'].sudo()
            doctor = None
            if doctor_id and str(doctor_id).strip() and str(doctor_id).strip() != '0' and str(doctor_id).strip() != 'any':
                try:
                    doctor = emp_obj.browse(int(doctor_id))
                    if not doctor.exists():
                        doctor = None
                except Exception:
                    doctor = None

            appt_obj = env['dental.appointment'].sudo()
            leave_obj = env['hr.leave'].sudo()

            if doctor:
                # Specific Doctor Validation
                overlap = appt_obj.search_count([
                    ('doctor_id', '=', doctor.id),
                    ('state', 'not in', ['cancelled', 'no_show']),
                    ('date_start', '<', dt_end),
                    ('date_end', '>', dt_start),
                ])
                if overlap > 0:
                    action = request.make_json_response({
                        'success': False,
                        'error': 'Doctor %s is already booked for this time slot (%s - %s). Please pick another time or choose Any Specialist.' % (doctor.name, appointment_time, dt_end.strftime('%H:%M'))
                    })
                    doctor = None
                else:
                    leaves = leave_obj.search_count([
                        ('employee_id', '=', doctor.id),
                        ('state', '=', 'validate'),
                        ('date_from', '<', dt_end),
                        ('date_to', '>', dt_start),
                    ])
                    if leaves > 0:
                        action = request.make_json_response({
                            'success': False,
                            'error': 'Doctor %s is on scheduled leave during this time. Please pick another time.' % doctor.name
                        })
                        doctor = None
            else:
                # Any Doctor: Find first free active dentist
                all_dentists = emp_obj.search([('is_dentist', '=', True), ('active', '=', True)], order='id asc')
                if not all_dentists:
                    all_dentists = emp_obj.search([('id', 'in', [1, 4])], order='id asc')

                for d in all_dentists:
                    overlap = appt_obj.search_count([
                        ('doctor_id', '=', d.id),
                        ('state', 'not in', ['cancelled', 'no_show']),
                        ('date_start', '<', dt_end),
                        ('date_end', '>', dt_start),
                    ])
                    if overlap == 0:
                        leaves = leave_obj.search_count([
                            ('employee_id', '=', d.id),
                            ('state', '=', 'validate'),
                            ('date_from', '<', dt_end),
                            ('date_to', '>', dt_start),
                        ])
                        if leaves == 0:
                            doctor = d
                            break

                if not doctor:
                    action = request.make_json_response({
                        'success': False,
                        'error': 'All dental specialists are fully booked for this time slot. Please choose another date or time.'
                    })

            if doctor:
                # Resolve Patient
                partner_obj = env['res.partner'].sudo()
                patient = None

                if patient_type == 'returning' and patient_id:
                    try:
                        patient = partner_obj.browse(int(patient_id))
                        if not patient.exists():
                            patient = None
                    except Exception:
                        patient = None

                if not patient:
                    # New patient or identification fallback
                    if not name:
                        action = request.make_json_response({'success': False, 'error': 'Please enter your full name.'})
                    elif not phone:
                        action = request.make_json_response({'success': False, 'error': 'Please enter your mobile phone number.'})
                    else:
                        clean_digits = ''.join([c for c in phone if c.isdigit()])
                        existing = partner_obj.search([
                            ('is_dental_patient', '=', True),
                            ('phone', '=', phone)
                        ], limit=1)
                        if not existing and clean_digits and len(clean_digits) >= 7:
                            existing = partner_obj.search([
                                ('is_dental_patient', '=', True),
                                ('phone', 'ilike', clean_digits)
                            ], limit=1)

                        if existing:
                            patient = existing
                            # Update missing fields safely
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

                if patient:
                    # Resolve Treatment
                    treatment = None
                    if treatment_id:
                        try:
                            treatment = env['product.template'].sudo().browse(int(treatment_id))
                            if not treatment.exists():
                                treatment = None
                        except Exception:
                            treatment = None
                    if not treatment:
                        # Fallback to general consultation treatment
                        treatment = env['product.template'].sudo().search([('is_dental_treatment', '=', True)], limit=1)

                    service_title = appt_type.name if appt_type else (treatment.name if treatment else 'Dental Appointment')
                    reason_text = service_title
                    if notes:
                        reason_text = '%s - %s' % (service_title, notes)

                    appt = appt_obj.create({
                        'patient_id': patient.id,
                        'doctor_id': doctor.id,
                        'appointment_type_id': appt_type.id if appt_type else False,
                        'treatment_id': treatment.id if treatment else False,
                        'branch_id': env.company.id,
                        'date_start': dt_start,
                        'date_end': dt_end,
                        'reason': reason_text,
                        'notes': notes,
                        'state': 'pending',
                        'priority': '1',
                    })

                    # Try email notification if template is configured
                    try:
                        template = env.ref('dental_appointment.email_template_appointment_confirmation', raise_if_not_found=False)
                        if template and patient.email:
                            template.sudo().send_mail(appt.id, force_send=False)
                    except Exception as mail_err:
                        log('Email notification skipped: %s' % str(mail_err), level='info')

                    action = request.make_json_response({
                        'success': True,
                        'appointment_id': appt.id,
                        'appointment_name': appt.name,
                        'patient_name': patient.name,
                        'patient_id': patient.dental_patient_id or ('PT-%05d' % patient.id),
                        'doctor_name': doctor.name,
                        'doctor_specialization': doctor.specialization or 'Dental Specialist',
                        'service_name': service_title,
                        'duration_min': int(duration),
                        'date_str': appointment_date,
                        'date_formatted': dt_start.strftime('%A, %B %d, %Y'),
                        'time_str': appointment_time,
                        'time_formatted': dt_start.strftime('%I:%M %p'),
                        'status': 'Pending Confirmation',
                    })
except Exception as e:
    log('book_appointment error: %s' % str(e), level='error')
    action = request.make_json_response({'success': False, 'error': str(e)})
"""

# Insert / Update Action 980 (check_patient)
cur.execute("""
INSERT INTO ir_act_server (id, name, model_id, usage, state, website_path, code, type, binding_type, create_uid, write_uid, create_date, write_date)
VALUES (980, %s, 91, 'ir_actions_server', 'code', 'check_patient', %s, 'ir.actions.server', 'action', 2, 2, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET code = EXCLUDED.code, website_path = 'check_patient', write_date = NOW();
""", (json.dumps({"en_US": "Dental Check Patient"}), check_patient_code))

# Insert / Update Action 981 (book_appointment)
cur.execute("""
INSERT INTO ir_act_server (id, name, model_id, usage, state, website_path, code, type, binding_type, create_uid, write_uid, create_date, write_date)
VALUES (981, %s, 91, 'ir_actions_server', 'code', 'book_appointment', %s, 'ir.actions.server', 'action', 2, 2, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET code = EXCLUDED.code, website_path = 'book_appointment', write_date = NOW();
""", (json.dumps({"en_US": "Dental Book Appointment"}), book_appointment_code))

# Insert / Update Action 982 (get_slots)
cur.execute("""
INSERT INTO ir_act_server (id, name, model_id, usage, state, website_path, code, type, binding_type, create_uid, write_uid, create_date, write_date)
VALUES (982, %s, 91, 'ir_actions_server', 'code', 'get_slots', %s, 'ir.actions.server', 'action', 2, 2, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET code = EXCLUDED.code, website_path = 'get_slots', write_date = NOW();
""", (json.dumps({"en_US": "Dental Get Available Slots"}), get_slots_code))

# Ensure public group access
for act_id in [980, 981, 982]:
    cur.execute("INSERT INTO ir_act_server_group_rel (act_id, gid) VALUES (%s, 1) ON CONFLICT DO NOTHING;", (act_id,))

conn.commit()
conn.close()
print("All 3 website server actions (980, 981, 982) configured successfully!")
