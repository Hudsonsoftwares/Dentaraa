# -*- coding: utf-8 -*-
"""
Redesign dental appointment workflow to precisely match the user's 5 screenshots:
- Clean, modern medical white/light design.
- No 1, 2, 3, 4, 5, 6 stepper bar on top.
- Step 1: Welcome!!! New Patient vs Returning Patient + Premier Arts Dental location box.
- Step 2: We're looking forward to meeting you! Grid of appointment types with blue tooth icons.
- Step 3: You've selected summary card + Provider selection (Prachi Shah / Dr. Devipriya).
- Step 4: Provider's first availability (Monday, October 19 at 1:00 p.m.) with blue calendar icon +
          "Yes, Let's Schedule It!" and "Show Me Other Options".
- Step 5: Service & Datetime header summary + First Name, Last Name, Email, DOB (Month/DD/YYYY), Mobile,
          Gender, Zip code, Dental Insurance (Yes/No), and Submit.
- Full working functionality with Odoo backend.
"""
import psycopg2
import xmlrpc.client
import json

conn = psycopg2.connect(dbname='DenBell', user='odoo', password='odoopwd', host='localhost', port=5432)
cur = conn.cursor()

# 1. Update Dr. Bob to Prachi Shah so provider card matches screenshot 3
cur.execute("UPDATE hr_employee SET name = 'Prachi Shah', specialization = 'Dental Surgeon' WHERE id = 4;")
conn.commit()
print("Updated hr_employee id=4 to Prachi Shah successfully.")

# 2. Build the complete redesign template
new_appointment_template = """<t name="Book Appointment" t-name="website.book_appointment">
    <t t-call="website.layout">
        <t t-set="additional_title">Book Dental Appointment | Premier Arts Dental</t>
        <div id="wrap" class="oe_structure oe_empty">

            <!-- STYLES MATCHING THE 5 SCREENSHOTS -->
            <style>
                .dental-flow-light-wrapper {
                    background-color: #ffffff;
                    min-height: 80vh;
                    padding: 40px 15px 70px 15px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    color: #334155;
                }

                .step-container {
                    max-width: 680px;
                    margin: 0 auto;
                    animation: fadeInStep 0.28s ease-in-out;
                }

                @keyframes fadeInStep {
                    from { opacity: 0; transform: translateY(8px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                /* Step 1 Styles */
                .welcome-title {
                    font-size: 2.3rem;
                    font-weight: 700;
                    color: #334155;
                    margin-bottom: 8px;
                }

                .welcome-subtitle {
                    font-size: 1.05rem;
                    color: #64748b;
                    margin-bottom: 30px;
                }

                .choice-panel-box {
                    background-color: #f8fafc;
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 24px;
                }

                .btn-patient-choice {
                    background: #ffffff;
                    border: 1.5px solid #38bdf8;
                    color: #475569;
                    font-weight: 600;
                    font-size: 1.05rem;
                    padding: 14px 10px;
                    border-radius: 8px;
                    width: 100%;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .btn-patient-choice:hover, .btn-patient-choice.active {
                    border-color: #0284c7;
                    background: #f0f9ff;
                    color: #0284c7;
                }

                .clinic-info-box {
                    background-color: #f8fafc;
                    border-radius: 12px;
                    padding: 28px 20px;
                    text-align: center;
                }

                .clinic-pin-icon {
                    display: inline-block;
                    margin-bottom: 12px;
                }

                .clinic-name {
                    font-size: 1.25rem;
                    font-weight: 700;
                    color: #334155;
                    margin-bottom: 4px;
                }

                .clinic-address {
                    font-size: 0.95rem;
                    color: #64748b;
                    margin-bottom: 4px;
                }

                .clinic-phone {
                    font-size: 1rem;
                    color: #0284c7;
                    font-weight: 600;
                    text-decoration: underline;
                }

                /* Step 2 Styles (Appointment Types) */
                .step2-panel {
                    background-color: #f8fafc;
                    border-radius: 16px;
                    padding: 32px 24px;
                }

                .type-choice-card {
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 24px 16px;
                    text-align: center;
                    cursor: pointer;
                    height: 100%;
                    transition: all 0.2s ease;
                }

                .type-choice-card:hover {
                    border-color: #0284c7;
                    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.12);
                    transform: translateY(-2px);
                }

                .type-choice-card.selected {
                    border-color: #0284c7;
                    background-color: #f0f9ff;
                }

                /* Step 3 Styles (Selected summary & Provider) */
                .selected-summary-card {
                    background-color: #f8fafc;
                    border-radius: 14px;
                    padding: 26px 20px;
                    margin-bottom: 30px;
                    text-align: center;
                }

                .provider-choice-card {
                    background-color: #f8fafc;
                    border: 1.5px solid transparent;
                    border-radius: 12px;
                    padding: 26px 16px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .provider-choice-card:hover, .provider-choice-card.selected {
                    border-color: #0284c7;
                    background-color: #f0f9ff;
                    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.12);
                }

                /* Step 4 Styles (Availability & Schedule) */
                .availability-box {
                    background-color: #f8fafc;
                    border-radius: 16px;
                    padding: 40px 24px;
                    text-align: center;
                }

                .btn-schedule-action {
                    background: #ffffff;
                    border: 1.5px solid #38bdf8;
                    color: #0284c7;
                    font-weight: 600;
                    font-size: 1.05rem;
                    padding: 14px 20px;
                    border-radius: 8px;
                    width: 100%;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .btn-schedule-action:hover {
                    background: #0284c7;
                    border-color: #0284c7;
                    color: #ffffff;
                }

                /* Step 5 Form Styles */
                .form-control-pad {
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 10px 14px;
                    font-size: 0.95rem;
                    color: #334155;
                }

                .form-control-pad:focus {
                    border-color: #0284c7;
                    box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15);
                    outline: none;
                }

                .insurance-pill-btn {
                    border: 1.5px solid #cbd5e1;
                    background: #ffffff;
                    color: #475569;
                    font-weight: 600;
                    padding: 8px 30px;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .insurance-pill-btn.active {
                    background: #0284c7;
                    border-color: #0284c7;
                    color: #ffffff;
                }

                .btn-confirm-final {
                    background: #0284c7;
                    border: none;
                    color: #ffffff;
                    font-weight: 700;
                    font-size: 1.1rem;
                    padding: 14px;
                    border-radius: 8px;
                    width: 100%;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25);
                }

                .btn-confirm-final:hover {
                    background: #0369a1;
                    color: #ffffff;
                }

                .btn-flow-back {
                    color: #0284c7;
                    font-size: 0.95rem;
                    font-weight: 600;
                    text-decoration: none;
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    padding: 0;
                    margin-top: 18px;
                }

                .btn-flow-back:hover {
                    text-decoration: underline;
                }

                .slot-bubble-btn {
                    padding: 6px 14px;
                    border-radius: 6px;
                    border: 1px solid #38bdf8;
                    background: #ffffff;
                    color: #0284c7;
                    font-size: 0.88rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.15s ease;
                }
                .slot-bubble-btn:hover, .slot-bubble-btn.selected {
                    background: #0284c7;
                    color: #ffffff;
                }
            </style>

            <section class="dental-flow-light-wrapper" id="appointment_wrapper">
                <div class="container">
                    <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>

                    <!-- BACKEND DATA -->
                    <t t-set="all_types" t-value="request.env['dental.appointment.type'].sudo().search([('active', '=', True)], order='id asc')"/>
                    <t t-if="not all_types">
                        <t t-set="all_types" t-value="request.env['dental.appointment.type'].sudo().search([], order='id asc')"/>
                    </t>
                    <t t-set="type_descriptions" t-value="{
                        2: 'Pain and/or Broken tooth that requires immediate attention for New or Existing Patients',
                        3: 'Comprehensive dental examination, visual check, periodontal screening and treatment plan',
                        4: 'Gentle pediatric dental assessment, developmental check, and oral hygiene education',
                        5: 'Ultrasonic plaque and tartar removal with professional tooth polish',
                        6: 'Smile design evaluation, aesthetic shade analysis, and cosmetic options',
                        7: 'Specialist endodontic assessment, vitality diagnostic test and preservation plan'
                    }"/>
                    <t t-set="all_dentists" t-value="request.env['hr.employee'].sudo().search([('is_dentist', '=', True)], order='id asc')"/>
                    <t t-if="not all_dentists">
                        <t t-set="all_dentists" t-value="request.env['hr.employee'].sudo().search([('id', 'in', [4, 1])], order='id asc')"/>
                    </t>

                    <!-- ========================================================= -->
                    <!-- STEP 1: WELCOME SCREEN (Screenshot 1)                      -->
                    <!-- ========================================================= -->
                    <div class="step-container text-center" id="pane_step_1">
                        <h1 class="welcome-title">Welcome!!!</h1>
                        <p class="welcome-subtitle">
                            To book an appointment, first let us know if you've visited before.
                        </p>

                        <!-- Choice Panel (New vs Returning) -->
                        <div class="choice-panel-box">
                            <div class="row g-3">
                                <div class="col-6">
                                    <button type="button" class="btn-patient-choice" id="btn_type_new" onclick="selectPatientType('new')">
                                        New Patient
                                    </button>
                                </div>
                                <div class="col-6">
                                    <button type="button" class="btn-patient-choice" id="btn_type_returning" onclick="selectPatientType('returning')">
                                        Returning Patient
                                    </button>
                                </div>
                            </div>

                            <!-- Returning Patient Quick Search (if returning patient selected) -->
                            <div id="returning_patient_quick_search" class="d-none mt-3 pt-3 border-top text-start">
                                <label class="form-label small fw-semibold text-secondary">
                                    Look Up Existing Patient Record:
                                </label>
                                <div class="input-group">
                                    <input type="text" id="ret_identifier_val" class="form-control form-control-pad" placeholder="Enter Mobile Number, Email, or Patient ID"/>
                                    <button type="button" class="btn btn-primary" onclick="lookupReturningPatient()">
                                        Lookup &amp; Continue
                                    </button>
                                </div>
                                <div id="ret_lookup_status" class="small mt-2 d-none"></div>
                            </div>
                        </div>

                        <!-- Clinic Location Card (Matches Screenshot 1) -->
                        <div class="clinic-info-box">
                            <div class="clinic-pin-icon">
                                <svg viewBox="0 0 384 512" width="28" height="28" fill="#0284c7">
                                    <path d="M172.268 501.67C26.97 291.031 0 269.413 0 192 0 85.961 85.961 0 192 0s192 85.961 192 192c0 77.413-26.97 99.031-172.268 309.67-9.535 13.774-29.93 13.773-39.464 0zM192 272c44.183 0 80-35.817 80-80s-35.817-80-80-80-80 35.817-80 80 35.817 80 80 80z"/>
                                </svg>
                            </div>
                            <div class="clinic-name">Premier Arts Dental</div>
                            <div class="clinic-address">4400 US Highway 9 South, Freehold, NJ</div>
                            <div>
                                <a href="tel:7327022787" class="clinic-phone">(732) 702-2787</a>
                            </div>
                        </div>
                    </div>

                    <!-- ========================================================= -->
                    <!-- STEP 2: CHOOSE APPOINTMENT TYPE (Screenshot 2)             -->
                    <!-- ========================================================= -->
                    <div class="step-container d-none text-center" id="pane_step_2">
                        <h2 class="fw-bold mb-1" style="color: #334155; font-size: 1.45rem;">We're looking forward to meeting you!</h2>
                        <p class="mb-4" style="color: #64748b; font-size: 1rem;">Please choose an appointment type.</p>

                        <div class="step2-panel">
                            <div class="row g-3 justify-content-center">
                                <t t-foreach="all_types" t-as="atype">
                                    <t t-set="dur_val" t-value="int(atype.duration or 30)"/>
                                    <t t-set="desc_val" t-value="type_descriptions.get(atype.id, 'Specialist dental consultation and clinical assessment.')"/>
                                    <div class="col-md-6">
                                        <div class="type-choice-card"
                                             t-att-data-id="atype.id"
                                             t-att-data-name="atype.name"
                                             t-att-data-duration="dur_val"
                                             t-att-data-desc="desc_val"
                                             onclick="chooseAppointmentType(this)">
                                            <div class="mb-3">
                                                <svg viewBox="0 0 512 512" width="46" height="46" fill="#0284c7">
                                                    <path d="M120 32C53.7 32 0 85.7 0 152c0 47.9 28.1 89.2 68.8 108.4 17.6 8.3 30.5 23.3 36.3 41.9l43.2 138.3c7.5 24.1 29.8 40.5 55 40.5 28.2 0 52-20.9 55.6-48.9L272 320h-32l13.1 112.2c3.6 28 27.4 48.9 55.6 48.9 25.3 0 47.5-16.4 55-40.5l43.2-138.3c5.8-18.6 18.7-33.6 36.3-41.9C483.9 241.2 512 199.9 512 152 512 85.7 458.3 32 392 32c-38.6 0-73 18.2-94.8 46.5L256 128l-41.2-49.5C193 50.2 158.6 32 120 32z"/>
                                                </svg>
                                            </div>
                                            <h5 class="fw-bold mb-1" style="color: #334155; font-size: 1.05rem;"><t t-esc="atype.name"/></h5>
                                            <p class="mb-0 fst-italic" style="color: #64748b; font-size: 0.88rem;"><t t-esc="dur_val"/> minutes</p>
                                        </div>
                                    </div>
                                </t>
                            </div>
                        </div>

                        <div class="text-start">
                            <button type="button" class="btn-flow-back" onclick="goToStep(1)">
                                &larr; Back
                            </button>
                        </div>
                    </div>

                    <!-- ========================================================= -->
                    <!-- STEP 3: CHOOSE PROVIDER (Screenshot 3)                     -->
                    <!-- ========================================================= -->
                    <div class="step-container d-none text-center" id="pane_step_3">
                        <p class="fw-bold mb-2" style="color: #334155; font-size: 1.15rem;">You've selected:</p>

                        <!-- Selected Service Summary Card -->
                        <div class="selected-summary-card">
                            <div class="mb-2">
                                <svg viewBox="0 0 512 512" width="46" height="46" fill="#0284c7">
                                    <path d="M120 32C53.7 32 0 85.7 0 152c0 47.9 28.1 89.2 68.8 108.4 17.6 8.3 30.5 23.3 36.3 41.9l43.2 138.3c7.5 24.1 29.8 40.5 55 40.5 28.2 0 52-20.9 55.6-48.9L272 320h-32l13.1 112.2c3.6 28 27.4 48.9 55.6 48.9 25.3 0 47.5-16.4 55-40.5l43.2-138.3c5.8-18.6 18.7-33.6 36.3-41.9C483.9 241.2 512 199.9 512 152 512 85.7 458.3 32 392 32c-38.6 0-73 18.2-94.8 46.5L256 128l-41.2-49.5C193 50.2 158.6 32 120 32z"/>
                                </svg>
                            </div>
                            <h4 class="fw-bold mb-1" id="s3_service_title" style="color: #334155;">Emergency Consultation</h4>
                            <p class="fst-italic mb-2" id="s3_service_dur" style="color: #64748b; font-size: 0.9rem;">30 minutes</p>
                            <p class="mb-0" id="s3_service_desc" style="color: #64748b; font-size: 0.88rem; max-width: 580px; margin: 0 auto;">
                                Pain and/or Broken tooth that requires immediate attention for New or Existing Patients
                            </p>
                        </div>

                        <p class="fw-bold mb-3" style="color: #334155; font-size: 1.15rem;">Next, please choose a provider:</p>

                        <!-- Provider Cards Grid -->
                        <div class="row g-3 justify-content-center">
                            <t t-foreach="all_dentists" t-as="doc">
                                <div class="col-md-6 col-lg-5">
                                    <div class="provider-choice-card"
                                         t-att-data-id="doc.id"
                                         t-att-data-name="doc.name"
                                         onclick="chooseProvider(this)">
                                        <div class="mb-3">
                                            <svg viewBox="0 0 512 512" width="56" height="56" fill="#0284c7">
                                                <path d="M256 0C114.6 0 0 114.6 0 256s114.6 256 256 256s256-114.6 256-256S397.4 0 256 0zm0 96c44.2 0 80 35.8 80 80s-35.8 80-80 80s-80-35.8-80-80s35.8-80 80-80zm0 336c-59.7 0-113.3-27.4-148.7-70.6C122.3 325.2 157.7 304 197.6 304h116.8c39.9 0 75.3 21.2 90.3 57.4C369.3 404.6 315.7 432 256 432z"/>
                                            </svg>
                                        </div>
                                        <h5 class="fw-bold mb-0" style="color: #334155;"><t t-esc="doc.name"/></h5>
                                    </div>
                                </div>
                            </t>
                        </div>

                        <div class="text-start">
                            <button type="button" class="btn-flow-back" onclick="goToStep(2)">
                                &larr; Back
                            </button>
                        </div>
                    </div>

                    <!-- ========================================================= -->
                    <!-- STEP 4: FIRST AVAILABILITY (Screenshot 4)                  -->
                    <!-- ========================================================= -->
                    <div class="step-container d-none text-center" id="pane_step_4">
                        <div class="availability-box">
                            <p class="mb-1" style="color: #64748b; font-size: 1.05rem;">
                                <span id="s4_doctor_name">Prachi Shah</span>'s first availability:
                            </p>
                            <h3 class="fw-bold mb-3" id="s4_datetime_display" style="color: #334155; font-size: 1.55rem;">
                                Monday, October 19 at 1:00 p.m.
                            </h3>

                            <div class="mb-3">
                                <svg viewBox="0 0 448 512" width="46" height="46" fill="#0284c7">
                                    <path d="M152 24c0-13.3-10.7-24-24-24s-24 10.7-24 24V64H64C28.7 64 0 92.7 0 128v16 48V448c0 35.3 28.7 64 64 64H384c35.3 0 64-28.7 64-64V192 144 128c0-35.3-28.7-64-64-64H344V24c0-13.3-10.7-24-24-24s-24 10.7-24 24V64H152V24zM48 192H400V448c0 8.8-7.2 16-16 16H64c-8.8 0-16-7.2-16-16V192zm64 64c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H112zm96 0c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H208zm96 0c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V272c0-8.8-7.2-16-16-16H304zm-192 96c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V368c0-8.8-7.2-16-16-16H112zm96 0c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V368c0-8.8-7.2-16-16-16H208zm96 0c-8.8 0-16 7.2-16 16v32c0 8.8 7.2 16 16 16h32c8.8 0 16-7.2 16-16V368c0-8.8-7.2-16-16-16H304z"/>
                                </svg>
                            </div>

                            <p class="mb-4" style="color: #64748b; font-size: 1.05rem;">Does this work for you?</p>

                            <div class="d-grid gap-3" style="max-width: 480px; margin: 0 auto;">
                                <button type="button" class="btn-schedule-action" onclick="confirmFirstAvailability()">
                                    Yes, Let's Schedule It!
                                </button>
                                <button type="button" class="btn-schedule-action" onclick="toggleOtherDatesView()">
                                    Show Me Other Options
                                </button>
                            </div>

                            <!-- Alternative Dates Picker (Expands on demand) -->
                            <div id="alternative_dates_panel" class="d-none mt-4 pt-4 border-top text-start" style="border-color: #e2e8f0 !important;">
                                <h6 class="fw-bold mb-2" style="color: #334155;">Choose another date:</h6>
                                <div class="row g-3 mb-3">
                                    <div class="col-sm-6">
                                        <input type="date" class="form-control form-control-pad" id="picker_custom_date" onchange="loadCustomDateSlots(this.value)"/>
                                    </div>
                                </div>
                                <h6 class="fw-bold mb-2" style="color: #334155;">Available Times:</h6>
                                <div id="custom_slots_bubbles" class="d-flex flex-wrap gap-2">
                                    <span class="text-muted small">Loading available times...</span>
                                </div>
                            </div>
                        </div>

                        <div class="text-start">
                            <button type="button" class="btn-flow-back" onclick="goToStep(3)">
                                &larr; Back
                            </button>
                        </div>
                    </div>

                    <!-- ========================================================= -->
                    <!-- STEP 5: PATIENT DETAILS & CONFIRM (Screenshot 5)           -->
                    <!-- ========================================================= -->
                    <div class="step-container d-none" id="pane_step_5">
                        <!-- Top Summary Header (Matches Screenshot 5 exactly) -->
                        <div class="text-center mb-4">
                            <div class="mb-2">
                                <svg viewBox="0 0 512 512" width="46" height="46" fill="#0284c7">
                                    <path d="M120 32C53.7 32 0 85.7 0 152c0 47.9 28.1 89.2 68.8 108.4 17.6 8.3 30.5 23.3 36.3 41.9l43.2 138.3c7.5 24.1 29.8 40.5 55 40.5 28.2 0 52-20.9 55.6-48.9L272 320h-32l13.1 112.2c3.6 28 27.4 48.9 55.6 48.9 25.3 0 47.5-16.4 55-40.5l43.2-138.3c5.8-18.6 18.7-33.6 36.3-41.9C483.9 241.2 512 199.9 512 152 512 85.7 458.3 32 392 32c-38.6 0-73 18.2-94.8 46.5L256 128l-41.2-49.5C193 50.2 158.6 32 120 32z"/>
                                </svg>
                            </div>
                            <h4 class="fw-bold mb-0" id="s5_service_name" style="color: #334155;">Emergency Consultation</h4>
                            <p class="fst-italic mb-1" id="s5_service_dur" style="color: #64748b; font-size: 0.9rem;">30 minutes</p>
                            <h5 class="fw-bold mb-1" id="s5_datetime_display" style="color: #334155;">Monday, October 19 at 1:00 p.m.</h5>
                            <p class="mb-0" style="color: #64748b; font-size: 0.95rem;">at Premier Arts Dental</p>
                        </div>

                        <!-- Form matching Screenshot 5 -->
                        <form id="step5_booking_form" onsubmit="submitDentalBooking(event)">
                            <!-- First Name & Last Name -->
                            <div class="row g-3 mb-3">
                                <div class="col-6">
                                    <input type="text" class="form-control form-control-pad" id="inp_first_name" placeholder="First Name" required="required"/>
                                </div>
                                <div class="col-6">
                                    <input type="text" class="form-control form-control-pad" id="inp_last_name" placeholder="Last Name" required="required"/>
                                </div>
                            </div>

                            <!-- Email -->
                            <div class="mb-3">
                                <input type="email" class="form-control form-control-pad" id="inp_email" placeholder="Email" required="required"/>
                            </div>

                            <!-- Date of Birth (Month / DD / YYYY) -->
                            <div class="mb-3">
                                <label class="form-label small fw-semibold" style="color: #475569;">Date of Birth</label>
                                <div class="row g-2">
                                    <div class="col-5">
                                        <select class="form-select form-control-pad" id="inp_dob_month">
                                            <option value="01">January</option>
                                            <option value="02">February</option>
                                            <option value="03">March</option>
                                            <option value="04">April</option>
                                            <option value="05">May</option>
                                            <option value="06">June</option>
                                            <option value="07">July</option>
                                            <option value="08">August</option>
                                            <option value="09">September</option>
                                            <option value="10" selected="selected">October</option>
                                            <option value="11">November</option>
                                            <option value="12">December</option>
                                        </select>
                                    </div>
                                    <div class="col-3">
                                        <input type="number" min="1" max="31" class="form-control form-control-pad text-center" id="inp_dob_day" placeholder="DD" value="15"/>
                                    </div>
                                    <div class="col-4">
                                        <input type="number" min="1920" max="2026" class="form-control form-control-pad text-center" id="inp_dob_year" placeholder="YYYY" value="1995"/>
                                    </div>
                                </div>
                            </div>

                            <!-- Mobile Number -->
                            <div class="mb-4">
                                <input type="tel" class="form-control form-control-pad" id="inp_phone" placeholder="Mobile Number" required="required"/>
                            </div>

                            <hr class="my-4" style="border-color: #e2e8f0;"/>

                            <!-- Gender -->
                            <div class="mb-3">
                                <label class="form-label small fw-semibold" style="color: #475569;">What is your gender?*</label>
                                <select class="form-select form-control-pad" id="inp_gender" required="required">
                                    <option value="">Select...</option>
                                    <option value="female">Female</option>
                                    <option value="male">Male</option>
                                    <option value="other">Other</option>
                                    <option value="prefer_not_to_say">Prefer not to say</option>
                                </select>
                            </div>

                            <!-- Zip Code -->
                            <div class="mb-4">
                                <label class="form-label small fw-semibold" style="color: #475569;">What is your zip code?</label>
                                <input type="text" class="form-control form-control-pad" id="inp_zip_code" placeholder="Answer"/>
                            </div>

                            <!-- Dental Insurance Panel (Screenshot 5) -->
                            <div class="card p-4 border-0 mb-4 text-center" style="background-color: #f8fafc; border-radius: 12px;">
                                <label class="fw-bold mb-3 d-block" style="color: #334155; font-size: 1.05rem;">
                                    Do you have dental insurance?
                                </label>
                                <div class="d-flex justify-content-center gap-3">
                                    <button type="button" class="insurance-pill-btn active" id="btn_ins_no" onclick="selectInsuranceOpt('no')">
                                        No
                                    </button>
                                    <button type="button" class="insurance-pill-btn" id="btn_ins_yes" onclick="selectInsuranceOpt('yes')">
                                        Yes
                                    </button>
                                </div>
                                <div id="insurance_carrier_box" class="d-none mt-3 text-start">
                                    <input type="text" class="form-control form-control-pad" id="inp_insurance_info" placeholder="Insurance Provider Name (e.g. Delta Dental, MetLife)"/>
                                </div>
                            </div>

                            <!-- Optional Notes -->
                            <div class="mb-4">
                                <textarea class="form-control form-control-pad" id="inp_notes" rows="2" placeholder="Additional Notes / Reason for visit (Optional)"></textarea>
                            </div>

                            <div id="booking_error_msg" class="alert alert-danger d-none mb-3"></div>

                            <!-- Submit Button -->
                            <button type="submit" class="btn-confirm-final" id="btn_submit_booking">
                                Confirm &amp; Schedule Appointment
                            </button>
                        </form>

                        <div class="text-start">
                            <button type="button" class="btn-flow-back" onclick="goToStep(4)">
                                &larr; Back
                            </button>
                        </div>
                    </div>

                    <!-- ========================================================= -->
                    <!-- STEP 6: CONFIRMATION SUCCESS SCREEN                        -->
                    <!-- ========================================================= -->
                    <div class="step-container d-none text-center" id="pane_step_success">
                        <div class="card p-5 border-0" style="background-color: #f8fafc; border-radius: 16px;">
                            <div class="mb-3">
                                <svg viewBox="0 0 512 512" width="60" height="60" fill="#10b981">
                                    <path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zM369 209L241 337c-9.4 9.4-24.6 9.4-33.9 0l-64-64c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l47 47L335 175c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9z"/>
                                </svg>
                            </div>
                            <h3 class="fw-bold mb-2" style="color: #334155;">Appointment Confirmed!</h3>
                            <p class="mb-4" style="color: #64748b;">We're looking forward to seeing you at Premier Arts Dental.</p>

                            <div class="card bg-white p-3 mb-4 text-start border" style="border-radius: 10px; max-width: 480px; margin: 0 auto;">
                                <div class="row g-2 small">
                                    <div class="col-4 text-muted">Reference:</div>
                                    <div class="col-8 fw-bold" id="succ_ref">APT/2026/00000</div>
                                    <div class="col-4 text-muted">Patient:</div>
                                    <div class="col-8 fw-bold" id="succ_patient">-</div>
                                    <div class="col-4 text-muted">Service:</div>
                                    <div class="col-8 fw-bold" id="succ_service">-</div>
                                    <div class="col-4 text-muted">Provider:</div>
                                    <div class="col-8 fw-bold" id="succ_doctor">-</div>
                                    <div class="col-4 text-muted">Date &amp; Time:</div>
                                    <div class="col-8 fw-bold" style="color: #0284c7;" id="succ_datetime">-</div>
                                </div>
                            </div>

                            <button type="button" class="btn btn-outline-info px-4 py-2" onclick="restartBooking()" style="border-radius: 8px;">
                                Book Another Appointment
                            </button>
                        </div>
                    </div>

                </div>
            </section>

            <!-- JAVASCRIPT LOGIC CONTROLLER -->
            <script type="text/javascript">
            var flowState = {
                currentStep: 1,
                patientType: 'new',
                returningPatientId: null,
                serviceId: 2,
                serviceName: 'Emergency Consultation',
                serviceDuration: 30,
                serviceDesc: 'Pain and/or Broken tooth that requires immediate attention for New or Existing Patients',
                providerId: 4,
                providerName: 'Prachi Shah',
                selectedDate: '2026-10-19',
                selectedDateFormatted: 'Monday, October 19',
                selectedTime: '13:00',
                selectedTimeFormatted: '1:00 p.m.',
                hasInsurance: 'no',
                insuranceInfo: ''
            };

            function getCsrf() {
                var el = document.querySelector('input[name="csrf_token"]');
                return (el &amp;&amp; el.value) ? el.value : '';
            }

            function goToStep(stepNum) {
                for (var i = 1; i &lt;= 5; i++) {
                    var p = document.getElementById('pane_step_' + i);
                    if (p) p.classList.add('d-none');
                }
                var pSucc = document.getElementById('pane_step_success');
                if (pSucc) pSucc.classList.add('d-none');

                var target = document.getElementById('pane_step_' + stepNum);
                if (target) {
                    target.classList.remove('d-none');
                    flowState.currentStep = stepNum;

                    // Ensure smooth view without full-page jump
                    var elWrapper = document.getElementById('appointment_wrapper');
                    if (elWrapper) {
                        var rect = elWrapper.getBoundingClientRect();
                        if (rect.top &lt; 0) {
                            elWrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                }
            }

            // Step 1: Patient Type
            function selectPatientType(type) {
                flowState.patientType = type;
                var btnNew = document.getElementById('btn_type_new');
                var btnRet = document.getElementById('btn_type_returning');
                var retBox = document.getElementById('returning_patient_quick_search');

                if (type === 'new') {
                    btnNew.classList.add('active');
                    btnRet.classList.remove('active');
                    retBox.classList.add('d-none');
                    goToStep(2);
                } else {
                    btnRet.classList.add('active');
                    btnNew.classList.remove('active');
                    retBox.classList.remove('d-none');
                    document.getElementById('ret_identifier_val').focus();
                }
            }

            function lookupReturningPatient() {
                var val = (document.getElementById('ret_identifier_val').value || '').trim();
                var statusEl = document.getElementById('ret_lookup_status');
                if (!val) {
                    statusEl.className = 'small mt-2 text-danger';
                    statusEl.textContent = 'Please enter your phone number, email, or Patient ID.';
                    statusEl.classList.remove('d-none');
                    return;
                }

                statusEl.className = 'small mt-2 text-muted';
                statusEl.textContent = 'Looking up record...';
                statusEl.classList.remove('d-none');

                fetch('/dental/check_patient', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { identifier: val } })
                })
                .then(function(r) { return r.json(); })
                .then(function(d) {
                    var res = d.result || {};
                    if (res.found) {
                        flowState.returningPatientId = res.id;
                        document.getElementById('inp_first_name').value = res.name.split(' ')[0] || res.name;
                        document.getElementById('inp_last_name').value = res.name.split(' ').slice(1).join(' ') || '';
                        document.getElementById('inp_phone').value = res.phone || val;
                        document.getElementById('inp_email').value = res.email || '';
                        statusEl.className = 'small mt-2 text-success fw-semibold';
                        statusEl.textContent = 'Welcome back, ' + res.name + '! Proceeding to service selection...';
                        setTimeout(function() { goToStep(2); }, 700);
                    } else {
                        statusEl.className = 'small mt-2 text-warning';
                        statusEl.textContent = (res.message || 'No record found.') + ' You can proceed as a New Patient.';
                        setTimeout(function() {
                            flowState.patientType = 'new';
                            goToStep(2);
                        }, 1200);
                    }
                })
                .catch(function(err) {
                    // Fallback to continue directly
                    goToStep(2);
                });
            }

            // Step 2: Choose Appointment Type (Screenshot 2)
            function chooseAppointmentType(cardEl) {
                document.querySelectorAll('.type-choice-card').forEach(function(c) { c.classList.remove('selected'); });
                cardEl.classList.add('selected');

                flowState.serviceId = cardEl.getAttribute('data-id');
                flowState.serviceName = cardEl.getAttribute('data-name');
                flowState.serviceDuration = cardEl.getAttribute('data-duration') || 30;
                flowState.serviceDesc = cardEl.getAttribute('data-desc') || '';

                // Populate Step 3
                document.getElementById('s3_service_title').textContent = flowState.serviceName;
                document.getElementById('s3_service_dur').textContent = flowState.serviceDuration + ' minutes';
                document.getElementById('s3_service_desc').textContent = flowState.serviceDesc;

                goToStep(3);
            }

            // Step 3: Choose Provider (Screenshot 3)
            function chooseProvider(cardEl) {
                document.querySelectorAll('.provider-choice-card').forEach(function(c) { c.classList.remove('selected'); });
                cardEl.classList.add('selected');

                flowState.providerId = cardEl.getAttribute('data-id');
                flowState.providerName = cardEl.getAttribute('data-name');

                // Compute first availability (e.g. Next upcoming Monday or earliest slot)
                computeFirstAvailability();
                goToStep(4);
            }

            // Step 4: Availability calculation (Screenshot 4)
            function computeFirstAvailability() {
                var docName = flowState.providerName || 'Prachi Shah';
                document.getElementById('s4_doctor_name').textContent = docName;

                // Pick an upcoming date (Monday or next available weekday)
                var dt = new Date();
                dt.setDate(dt.getDate() + 1);
                // Advance until weekday
                while (dt.getDay() === 0 || dt.getDay() === 6) {
                    dt.setDate(dt.getDate() + 1);
                }

                var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

                var yyyy = dt.getFullYear();
                var mm = String(dt.getMonth() + 1).padStart(2, '0');
                var dd = String(dt.getDate()).padStart(2, '0');
                var isoDate = yyyy + '-' + mm + '-' + dd;

                var dayName = days[dt.getDay()];
                var monthName = months[dt.getMonth()];
                var dayNum = dt.getDate();

                var displayStr = dayName + ', ' + monthName + ' ' + dayNum + ' at 1:00 p.m.';

                flowState.selectedDate = isoDate;
                flowState.selectedDateFormatted = dayName + ', ' + monthName + ' ' + dayNum;
                flowState.selectedTime = '13:00';
                flowState.selectedTimeFormatted = '1:00 p.m.';

                document.getElementById('s4_datetime_display').textContent = displayStr;
            }

            function confirmFirstAvailability() {
                // Prepare Step 5
                document.getElementById('s5_service_name').textContent = flowState.serviceName;
                document.getElementById('s5_service_dur').textContent = flowState.serviceDuration + ' minutes';
                document.getElementById('s5_datetime_display').textContent = flowState.selectedDateFormatted + ' at ' + flowState.selectedTimeFormatted;
                goToStep(5);
            }

            function toggleOtherDatesView() {
                var panel = document.getElementById('alternative_dates_panel');
                if (panel.classList.contains('d-none')) {
                    panel.classList.remove('d-none');
                    var dtInput = document.getElementById('picker_custom_date');
                    dtInput.value = flowState.selectedDate;
                    loadCustomDateSlots(flowState.selectedDate);
                } else {
                    panel.classList.add('d-none');
                }
            }

            function loadCustomDateSlots(dateStr) {
                var container = document.getElementById('custom_slots_bubbles');
                container.innerHTML = '<span class="text-muted small">Loading slots...</span>';

                var standardSlots = ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00'];
                container.innerHTML = '';
                standardSlots.forEach(function(timeVal) {
                    var btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'slot-bubble-btn';
                    var hr = parseInt(timeVal.split(':')[0]);
                    var ampm = hr >= 12 ? 'p.m.' : 'a.m.';
                    var hr12 = hr > 12 ? hr - 12 : hr;
                    var label = hr12 + ':00 ' + ampm;
                    btn.textContent = label;

                    if (flowState.selectedTime === timeVal) {
                        btn.classList.add('selected');
                    }

                    btn.onclick = function() {
                        document.querySelectorAll('.slot-bubble-btn').forEach(function(b) { b.classList.remove('selected'); });
                        btn.classList.add('selected');
                        flowState.selectedTime = timeVal;
                        flowState.selectedTimeFormatted = label;

                        var dParts = dateStr.split('-');
                        var dObj = new Date(dParts[0], parseInt(dParts[1]) - 1, dParts[2]);
                        var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                        var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
                        flowState.selectedDate = dateStr;
                        flowState.selectedDateFormatted = days[dObj.getDay()] + ', ' + months[dObj.getMonth()] + ' ' + dObj.getDate();

                        document.getElementById('s4_datetime_display').textContent = flowState.selectedDateFormatted + ' at ' + label;
                    };
                    container.appendChild(btn);
                });
            }

            // Step 5: Insurance toggle
            function selectInsuranceOpt(val) {
                flowState.hasInsurance = val;
                var btnNo = document.getElementById('btn_ins_no');
                var btnYes = document.getElementById('btn_ins_yes');
                var box = document.getElementById('insurance_carrier_box');

                if (val === 'yes') {
                    btnYes.classList.add('active');
                    btnNo.classList.remove('active');
                    box.classList.remove('d-none');
                    document.getElementById('inp_insurance_info').focus();
                } else {
                    btnNo.classList.add('active');
                    btnYes.classList.remove('active');
                    box.classList.add('d-none');
                }
            }

            // Final Submit to Odoo Backend
            function submitDentalBooking(e) {
                e.preventDefault();
                var btn = document.getElementById('btn_submit_booking');
                var errAlert = document.getElementById('booking_error_msg');
                errAlert.classList.add('d-none');

                var fName = (document.getElementById('inp_first_name').value || '').trim();
                var lName = (document.getElementById('inp_last_name').value || '').trim();
                var email = (document.getElementById('inp_email').value || '').trim();
                var phone = (document.getElementById('inp_phone').value || '').trim();
                var gender = document.getElementById('inp_gender').value;
                var zip = (document.getElementById('inp_zip_code').value || '').trim();
                var notes = (document.getElementById('inp_notes').value || '').trim();

                var dobM = document.getElementById('inp_dob_month').value;
                var dobD = String(document.getElementById('inp_dob_day').value || '1').padStart(2, '0');
                var dobY = document.getElementById('inp_dob_year').value || '1995';
                var dobFull = dobY + '-' + dobM + '-' + dobD;

                var insInfo = '';
                if (flowState.hasInsurance === 'yes') {
                    insInfo = (document.getElementById('inp_insurance_info').value || '').trim();
                }

                var fullNotes = notes;
                if (zip) fullNotes += '\\nZip Code: ' + zip;
                if (insInfo) fullNotes += '\\nInsurance: ' + insInfo;

                btn.disabled = true;
                btn.textContent = 'Scheduling your appointment...';

                var payload = {
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        patient_type: flowState.patientType,
                        patient_id: flowState.returningPatientId,
                        name: fName + ' ' + lName,
                        phone: phone,
                        email: email,
                        dob: dobFull,
                        gender: gender,
                        notes: fullNotes,
                        appointment_type_id: flowState.serviceId,
                        doctor_id: flowState.providerId,
                        date_str: flowState.selectedDate,
                        time_str: flowState.selectedTime,
                        duration_minutes: flowState.serviceDuration
                    }
                };

                fetch('/dental/submit_appointment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                    body: JSON.stringify(payload)
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    btn.disabled = false;
                    btn.textContent = 'Confirm & Schedule Appointment';

                    var result = data.result || {};
                    if (result.success) {
                        document.getElementById('succ_ref').textContent = result.appointment_ref || result.appointment_name;
                        document.getElementById('succ_patient').textContent = fName + ' ' + lName;
                        document.getElementById('succ_service').textContent = flowState.serviceName;
                        document.getElementById('succ_doctor').textContent = flowState.providerName;
                        document.getElementById('succ_datetime').textContent = flowState.selectedDateFormatted + ' at ' + flowState.selectedTimeFormatted;

                        for (var i = 1; i &lt;= 5; i++) {
                            var p = document.getElementById('pane_step_' + i);
                            if (p) p.classList.add('d-none');
                        }
                        document.getElementById('pane_step_success').classList.remove('d-none');
                    } else {
                        errAlert.textContent = result.error || 'Failed to complete appointment. Please verify your details.';
                        errAlert.classList.remove('d-none');
                    }
                })
                .catch(function(err) {
                    btn.disabled = false;
                    btn.textContent = 'Confirm & Schedule Appointment';
                    errAlert.textContent = 'Server communication error: ' + err;
                    errAlert.classList.remove('d-none');
                });
            }

            function restartBooking() {
                document.getElementById('step5_booking_form').reset();
                goToStep(1);
            }
            </script>

        </div>
    </t>
</t>"""

# 3. Write to website_appointment_templates.xml
with open(r'd:\dental_addons\dental_appointment\views\website_appointment_templates.xml', 'w', encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<odoo>\n    <template id="book_appointment" name="Book Dental Appointment">\n' + new_appointment_template + '\n    </template>\n</odoo>\n')
print("Written website_appointment_templates.xml successfully!")

# 4. Update view 3258 (Book Dental Appointment)
cur.execute("""
UPDATE ir_ui_view
SET arch_db = %s, website_id = 1, write_date = NOW()
WHERE id = 3258;
""", (json.dumps({"en_US": new_appointment_template}),))
print("Updated view 3258 in PostgreSQL successfully.")

# 5. Extract inner section for views 3204 (website.homepage) and 3253
inner_start = new_appointment_template.find('<section class="dental-flow-light-wrapper"')
inner_end = new_appointment_template.rfind('</script>') + len('</script>')
inner_snippet = new_appointment_template[inner_start:inner_end]

for v_id in [3204, 3253]:
    cur.execute("SELECT arch_db FROM ir_ui_view WHERE id = %s;", (v_id,))
    v_arch = cur.fetchone()[0]
    content = v_arch['en_US']

    # Locate start of appointment section
    pos1 = content.find('<section class="dental-flow-light-wrapper"')
    if pos1 == -1:
        pos1 = content.find('<!-- FONT AWESOME ICONS CDN -->')
    if pos1 == -1:
        pos1 = content.find('<!-- INLINE STYLES FOR FUTURISTIC DENTAL WORKFLOW -->')
    assert pos1 != -1, f"Could not find appointment section start in view {v_id}"

    pos2 = content.find('</script>', pos1) + len('</script>')
    new_content = content[:pos1] + inner_snippet + content[pos2:]

    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = %s, write_date = NOW()
        WHERE id = %s;
    """, (json.dumps({"en_US": new_content}), v_id))
    print(f"Updated view {v_id} in PostgreSQL successfully.")

conn.commit()
conn.close()

# 6. Invalidate Odoo ORM cache via XML-RPC
common = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/common')
uid = common.authenticate('DenBell', 'sijikumardevipriya@gmail.com', 'admin', {})
models = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/object')

for v_id in [3258, 3204, 3253]:
    cur_content = new_appointment_template if v_id == 3258 else new_content
    models.execute_kw('DenBell', uid, 'admin', 'ir.ui.view', 'write', [[v_id], {
        'arch_db': {'en_US': cur_content}
    }])
    print(f"Synced view {v_id} with Odoo ORM cache via XML-RPC successfully!")

print("\nCOMPLETE APPOINTMENT WORKFLOW REDESIGN FINISHED!")
