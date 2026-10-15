# -*- coding: utf-8 -*-
"""
Fix appointment page theme:
1. Load Font Awesome icons (v6 and v4.7) so all icons render properly.
2. Fix low-contrast fonts (override dark .text-muted, ensure high contrast white/cyan/light-slate for titles, descriptions, and labels).
3. Fix stepper circle and label contrast for inactive steps.
4. Eliminate disruptive auto-scrolling to top of website on each step selection.
"""
import psycopg2
import xmlrpc.client
import json

conn = psycopg2.connect(dbname='DenBell', user='odoo', password='odoopwd', host='localhost', port=5432)
cur = conn.cursor()

template_content = """<t name="Book Appointment" t-name="website.book_appointment">
    <t t-call="website.layout">
        <t t-set="additional_title">Book Dental Appointment | DenBell Dental Clinic</t>
        <div id="wrap" class="oe_structure oe_empty">

            <!-- FONT AWESOME ICONS CDN -->
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"/>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"/>

            <!-- INLINE STYLES FOR FUTURISTIC DENTAL WORKFLOW -->
            <style>
                :root {
                    --bg-dark: #050b18;
                    --bg-card: rgba(10, 18, 42, 0.92);
                    --bg-card-inner: rgba(16, 28, 62, 0.85);
                    --cyan-glow: #00f2fe;
                    --cyan-mid: #0284c7;
                    --cyan-light: #38bdf8;
                    --violet-accent: #8b5cf6;
                    --text-main: #f8fafc;
                    --text-muted: #cbd5e1;
                    --border-subtle: rgba(56, 189, 248, 0.22);
                    --border-active: #00f2fe;
                }

                .dental-flow-wrapper {
                    background: radial-gradient(circle at 50% 10%, #0d1e44 0%, #050b18 60%, #020611 100%);
                    min-height: 100vh;
                    color: var(--text-main);
                    padding: 40px 0 80px 0;
                    position: relative;
                    overflow: hidden;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                }

                /* Ensure all text-muted and body copy inside workflow is crisp, high-contrast readable */
                .dental-flow-wrapper .text-muted,
                .dental-flow-card .text-muted,
                .dental-flow-card p.text-muted,
                .dental-flow-card span.text-muted,
                .dental-flow-card div.text-muted,
                .flow-subtitle {
                    color: #cbd5e1 !important;
                }

                .dental-flow-wrapper p {
                    color: #e2e8f0;
                }

                /* Ambient Background Glows */
                .dental-flow-wrapper::before {
                    content: '';
                    position: absolute;
                    width: 600px;
                    height: 600px;
                    background: radial-gradient(circle, rgba(0, 242, 254, 0.12) 0%, transparent 70%);
                    top: -150px;
                    left: 50%;
                    transform: translateX(-50%);
                    pointer-events: none;
                    z-index: 0;
                }

                .dental-flow-wrapper::after {
                    content: '';
                    position: absolute;
                    width: 450px;
                    height: 450px;
                    background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
                    bottom: 50px;
                    right: -100px;
                    pointer-events: none;
                    z-index: 0;
                }

                /* Main Card */
                .dental-flow-card {
                    background: var(--bg-card);
                    backdrop-filter: blur(24px);
                    -webkit-backdrop-filter: blur(24px);
                    border: 1px solid var(--border-subtle);
                    border-radius: 24px;
                    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.65), 0 0 35px rgba(0, 242, 254, 0.1);
                    position: relative;
                    z-index: 1;
                    padding: 40px;
                    transition: all 0.3s ease;
                }

                @media (max-width: 768px) {
                    .dental-flow-card {
                        padding: 24px 18px;
                        border-radius: 18px;
                    }
                    .dental-flow-wrapper {
                        padding: 20px 0 50px 0;
                    }
                }

                /* Animated Step Progress Bar */
                .flow-progress-container {
                    margin-bottom: 40px;
                    position: relative;
                }

                .flow-progress-track {
                    position: absolute;
                    top: 22px;
                    left: 5%;
                    right: 5%;
                    height: 3px;
                    background: rgba(255, 255, 255, 0.15);
                    z-index: 1;
                    border-radius: 4px;
                }

                .flow-progress-fill {
                    position: absolute;
                    top: 0;
                    left: 0;
                    height: 100%;
                    width: 0%;
                    background: linear-gradient(90deg, #0284c7, #00f2fe);
                    box-shadow: 0 0 14px #00f2fe;
                    border-radius: 4px;
                    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .flow-steps-list {
                    display: flex;
                    justify-content: space-between;
                    position: relative;
                    z-index: 2;
                    list-style: none;
                    padding: 0;
                    margin: 0;
                }

                .flow-step-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    cursor: default;
                    position: relative;
                    flex: 1;
                }

                .flow-step-circle {
                    width: 44px;
                    height: 44px;
                    border-radius: 50%;
                    background: #0f1c3d;
                    border: 2px solid rgba(56, 189, 248, 0.35);
                    color: #cbd5e1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 700;
                    font-size: 1rem;
                    transition: all 0.3s ease;
                    margin-bottom: 8px;
                }

                .flow-step-item.active .flow-step-circle {
                    border-color: var(--cyan-glow);
                    background: linear-gradient(135deg, #0284c7, #00f2fe);
                    color: #050b18;
                    font-weight: 800;
                    box-shadow: 0 0 20px rgba(0, 242, 254, 0.7);
                    transform: scale(1.12);
                }

                .flow-step-item.completed .flow-step-circle {
                    border-color: var(--cyan-glow);
                    background: rgba(0, 242, 254, 0.18);
                    color: var(--cyan-glow);
                    cursor: pointer;
                }

                .flow-step-label {
                    font-size: 0.85rem;
                    color: #cbd5e1;
                    font-weight: 600;
                    text-align: center;
                    transition: color 0.3s ease;
                    white-space: nowrap;
                }

                .flow-step-item.active .flow-step-label {
                    color: var(--cyan-glow);
                    font-weight: 700;
                    text-shadow: 0 0 10px rgba(0, 242, 254, 0.5);
                }

                .flow-step-item.completed .flow-step-label {
                    color: #94a3b8;
                }

                @media (max-width: 576px) {
                    .flow-step-label {
                        display: none;
                    }
                    .flow-step-circle {
                        width: 36px;
                        height: 36px;
                        font-size: 0.85rem;
                    }
                    .flow-progress-track {
                        top: 18px;
                    }
                }

                /* Step Container Transitions */
                .flow-step-pane {
                    animation: dentalStepFade 0.32s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                }

                @keyframes dentalStepFade {
                    from {
                        opacity: 0;
                        transform: translateY(12px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                /* Titles and Typography */
                .flow-title {
                    font-size: 2.2rem;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                    color: #ffffff;
                    margin-bottom: 8px;
                }

                .flow-subtitle {
                    font-size: 1.05rem;
                    color: #cbd5e1 !important;
                    margin-bottom: 30px;
                    line-height: 1.5;
                }

                /* Welcome Screen Choice Cards */
                .choice-card-welcome {
                    background: var(--bg-card-inner);
                    border: 1.5px solid var(--border-subtle);
                    border-radius: 20px;
                    padding: 35px 25px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                    position: relative;
                    height: 100%;
                }

                .choice-card-welcome:hover {
                    border-color: var(--cyan-glow);
                    transform: translateY(-5px);
                    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.45), 0 0 25px rgba(0, 242, 254, 0.25);
                    background: rgba(22, 38, 82, 0.9);
                }

                .choice-card-welcome p {
                    color: #cbd5e1 !important;
                    font-size: 0.95rem;
                    line-height: 1.6;
                }

                .choice-icon-wrap {
                    width: 80px;
                    height: 80px;
                    border-radius: 20px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 20px;
                    font-size: 2.2rem;
                    transition: all 0.3s ease;
                }

                .choice-icon-new {
                    background: rgba(56, 189, 248, 0.18);
                    color: #38bdf8 !important;
                    border: 1.5px solid rgba(56, 189, 248, 0.45);
                }

                .choice-icon-returning {
                    background: rgba(139, 92, 246, 0.18);
                    color: #c084fc !important;
                    border: 1.5px solid rgba(139, 92, 246, 0.45);
                }

                .choice-card-welcome:hover .choice-icon-wrap {
                    transform: scale(1.1);
                    box-shadow: 0 0 22px currentColor;
                }

                .choice-badge {
                    display: inline-block;
                    padding: 5px 14px;
                    border-radius: 50px;
                    font-size: 0.78rem;
                    font-weight: 700;
                    letter-spacing: 0.6px;
                    text-transform: uppercase;
                    margin-bottom: 14px;
                }

                /* Selection Cards (Services and Dentists) */
                .selectable-card {
                    background: var(--bg-card-inner);
                    border: 1.5px solid var(--border-subtle);
                    border-radius: 16px;
                    padding: 22px;
                    cursor: pointer;
                    transition: all 0.25s ease;
                    position: relative;
                    height: 100%;
                }

                .selectable-card:hover {
                    border-color: rgba(56, 189, 248, 0.7);
                    background: rgba(22, 38, 82, 0.85);
                    transform: translateY(-3px);
                }

                .selectable-card.selected {
                    border-color: var(--cyan-glow);
                    background: rgba(16, 44, 90, 0.95);
                    box-shadow: 0 0 22px rgba(0, 242, 254, 0.3);
                }

                .card-check-indicator {
                    position: absolute;
                    top: 16px;
                    right: 16px;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                }

                .selectable-card.selected .card-check-indicator {
                    border-color: var(--cyan-glow);
                    background: var(--cyan-glow);
                    color: #050b18;
                    font-weight: bold;
                }

                .card-meta-pill {
                    font-size: 0.8rem;
                    padding: 4px 11px;
                    border-radius: 20px;
                    background: rgba(56, 189, 248, 0.15);
                    color: #38bdf8;
                    display: inline-block;
                    margin-right: 6px;
                    font-weight: 600;
                }

                /* Interactive Calendar */
                .calendar-container {
                    background: var(--bg-card-inner);
                    border: 1px solid var(--border-subtle);
                    border-radius: 18px;
                    padding: 22px;
                }

                .calendar-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 18px;
                }

                .calendar-nav-btn {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #ffffff;
                    border-radius: 10px;
                    width: 38px;
                    height: 38px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .calendar-nav-btn:hover {
                    background: var(--cyan-glow);
                    color: #050b18;
                    border-color: var(--cyan-glow);
                }

                .calendar-weekdays {
                    display: grid;
                    grid-template-columns: repeat(7, 1fr);
                    text-align: center;
                    font-size: 0.82rem;
                    color: #cbd5e1;
                    font-weight: 700;
                    margin-bottom: 10px;
                }

                .calendar-days-grid {
                    display: grid;
                    grid-template-columns: repeat(7, 1fr);
                    gap: 6px;
                }

                .cal-day-cell {
                    aspect-ratio: 1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    background: rgba(255, 255, 255, 0.05);
                    color: #f1f5f9;
                    cursor: pointer;
                    font-size: 0.92rem;
                    font-weight: 600;
                    transition: all 0.2s ease;
                    position: relative;
                }

                .cal-day-cell:hover:not(.disabled) {
                    background: rgba(56, 189, 248, 0.25);
                    border-color: var(--cyan-light);
                }

                .cal-day-cell.selected {
                    background: linear-gradient(135deg, #0284c7, #00f2fe) !important;
                    color: #050b18 !important;
                    font-weight: 800;
                    box-shadow: 0 0 18px rgba(0, 242, 254, 0.55);
                    border-color: var(--cyan-glow);
                }

                .cal-day-cell.today:not(.selected) {
                    border-color: var(--cyan-light);
                    color: var(--cyan-light);
                }

                .cal-day-cell.disabled {
                    opacity: 0.22;
                    cursor: not-allowed;
                    background: transparent;
                    border-color: transparent;
                }

                .cal-dot {
                    width: 4px;
                    height: 4px;
                    border-radius: 50%;
                    background: var(--cyan-glow);
                    margin-top: 3px;
                }

                /* Time Slots Grid */
                .slots-container {
                    background: var(--bg-card-inner);
                    border: 1px solid var(--border-subtle);
                    border-radius: 18px;
                    padding: 22px;
                    height: 100%;
                }

                .slot-period-title {
                    font-size: 0.85rem;
                    text-transform: uppercase;
                    letter-spacing: 0.8px;
                    color: var(--cyan-light);
                    font-weight: 700;
                    margin-bottom: 12px;
                    display: flex;
                    align-items: center;
                }

                .slot-btn {
                    padding: 10px 14px;
                    border-radius: 12px;
                    background: rgba(255, 255, 255, 0.06);
                    border: 1px solid rgba(56, 189, 248, 0.3);
                    color: #f1f5f9;
                    font-size: 0.92rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    width: 100%;
                    text-align: center;
                }

                .slot-btn:hover:not(.booked) {
                    background: rgba(56, 189, 248, 0.25);
                    border-color: var(--cyan-glow);
                    color: #ffffff;
                }

                .slot-btn.selected {
                    background: linear-gradient(135deg, #0284c7, #00f2fe) !important;
                    color: #050b18 !important;
                    font-weight: 800;
                    border-color: var(--cyan-glow);
                    box-shadow: 0 0 16px rgba(0, 242, 254, 0.45);
                }

                .slot-btn.booked {
                    opacity: 0.3;
                    cursor: not-allowed;
                    background: rgba(255, 255, 255, 0.02);
                    border-color: rgba(255, 255, 255, 0.08);
                    text-decoration: line-through;
                }

                /* Form Inputs */
                .flow-input-label {
                    font-size: 0.92rem;
                    font-weight: 600;
                    color: #f1f5f9;
                    margin-bottom: 8px;
                    display: block;
                }

                .flow-input {
                    background: rgba(13, 23, 48, 0.95);
                    border: 1.5px solid rgba(56, 189, 248, 0.32);
                    border-radius: 12px;
                    color: #ffffff;
                    padding: 12px 16px;
                    font-size: 0.95rem;
                    width: 100%;
                    transition: all 0.2s ease;
                }

                .flow-input:focus {
                    outline: none;
                    border-color: var(--cyan-glow);
                    box-shadow: 0 0 15px rgba(0, 242, 254, 0.35);
                    background: rgba(16, 28, 60, 0.98);
                    color: #ffffff;
                }

                .flow-input::placeholder {
                    color: #94a3b8;
                }

                /* Buttons */
                .flow-btn-primary {
                    background: linear-gradient(135deg, #0284c7 0%, #00f2fe 100%);
                    color: #050b18;
                    font-weight: 700;
                    font-size: 1rem;
                    border: none;
                    border-radius: 14px;
                    padding: 14px 28px;
                    cursor: pointer;
                    transition: all 0.25s ease;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 20px rgba(0, 242, 254, 0.35);
                }

                .flow-btn-primary:hover:not(:disabled) {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0, 242, 254, 0.55);
                    color: #020611;
                }

                .flow-btn-primary:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    box-shadow: none;
                }

                .flow-btn-secondary {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1.5px solid rgba(255, 255, 255, 0.25);
                    color: #f1f5f9;
                    font-weight: 600;
                    font-size: 0.95rem;
                    border-radius: 14px;
                    padding: 14px 24px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                }

                .flow-btn-secondary:hover {
                    background: rgba(255, 255, 255, 0.18);
                    color: #ffffff;
                    border-color: rgba(255, 255, 255, 0.4);
                }

                /* Review Summary Card */
                .review-card-box {
                    background: var(--bg-card-inner);
                    border: 1px solid var(--border-subtle);
                    border-radius: 18px;
                    padding: 24px;
                    margin-bottom: 24px;
                }

                .review-row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 14px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .review-row:last-child {
                    border-bottom: none;
                }

                .review-label {
                    color: #cbd5e1 !important;
                    font-size: 0.92rem;
                    display: flex;
                    align-items: center;
                    font-weight: 500;
                }

                .review-value {
                    font-weight: 600;
                    color: #ffffff;
                    font-size: 0.95rem;
                    text-align: right;
                }

                .review-edit-link {
                    color: var(--cyan-light);
                    font-size: 0.82rem;
                    text-decoration: none;
                    margin-left: 10px;
                    cursor: pointer;
                    font-weight: 600;
                }

                .review-edit-link:hover {
                    text-decoration: underline;
                    color: var(--cyan-glow);
                }

                /* Success Badge */
                .success-pulse-icon {
                    width: 90px;
                    height: 90px;
                    border-radius: 50%;
                    background: rgba(0, 242, 254, 0.15);
                    border: 2px solid var(--cyan-glow);
                    color: var(--cyan-glow);
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 2.8rem;
                    box-shadow: 0 0 35px rgba(0, 242, 254, 0.4);
                    margin-bottom: 24px;
                    animation: pulseGlow 2s infinite;
                }

                @keyframes pulseGlow {
                    0% { box-shadow: 0 0 20px rgba(0, 242, 254, 0.3); }
                    50% { box-shadow: 0 0 45px rgba(0, 242, 254, 0.7); }
                    100% { box-shadow: 0 0 20px rgba(0, 242, 254, 0.3); }
                }

                /* Security Disclaimer */
                .privacy-notice-box {
                    background: rgba(139, 92, 246, 0.12);
                    border: 1px solid rgba(139, 92, 246, 0.35);
                    border-radius: 12px;
                    padding: 14px 18px;
                    font-size: 0.88rem;
                    color: #e2e8f0;
                    display: flex;
                    align-items: flex-start;
                    margin-top: 18px;
                    line-height: 1.5;
                }
            </style>

            <!-- WORKFLOW SECTION -->
            <section class="dental-flow-wrapper" id="appointment">
                <div class="container">
                    <div class="row justify-content-center">
                        <div class="col-xl-9 col-lg-10 col-md-11">

                            <!-- DYNAMIC BACKEND DATA -->
                            <t t-set="all_types" t-value="request.env['dental.appointment.type'].sudo().search([('id', '!=', 1)], order='id asc')"/>
                            <t t-set="type_meta" t-value="{
                                2: {'dur': 30, 'price': 50, 'icon': 'fa-bolt', 'desc': 'Prompt clinical triage, immediate pain relief, diagnosis, and emergency care.'},
                                3: {'dur': 45, 'price': 75, 'icon': 'fa-user-md', 'desc': 'Comprehensive oral health assessment, full dental charting, and treatment plan.'},
                                4: {'dur': 30, 'price': 40, 'icon': 'fa-smile-o', 'desc': 'Gentle pediatric dental assessment, developmental check, and oral hygiene instruction.'},
                                5: {'dur': 45, 'price': 100, 'icon': 'fa-star', 'desc': 'Thorough ultrasonic plaque removal, scale and polish for a fresh smile.'},
                                6: {'dur': 45, 'price': 120, 'icon': 'fa-magic', 'desc': 'Aesthetic smile design evaluation, shade assessment, and whitening consultation.'},
                                7: {'dur': 60, 'price': 150, 'icon': 'fa-heartbeat', 'desc': 'Specialist endodontic diagnostics, vitality testing, and tooth preservation plan.'}
                            }"/>
                            <t t-set="all_dentists" t-value="request.env['hr.employee'].sudo().search([('is_dentist', '=', True)], order='id asc')"/>
                            <t t-if="not all_dentists">
                                <t t-set="all_dentists" t-value="request.env['hr.employee'].sudo().search([('id', 'in', [1, 4])], order='id asc')"/>
                            </t>

                            <!-- CARD CONTAINER -->
                            <div class="dental-flow-card" id="dental_flow_card">
                                <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>

                                <!-- PROGRESS TRACKER (6 STEPS) -->
                                <div class="flow-progress-container" id="flow_progress_bar">
                                    <div class="flow-progress-track">
                                        <div class="flow-progress-fill" id="progress_fill"></div>
                                    </div>
                                    <ul class="flow-steps-list">
                                        <li class="flow-step-item active" data-step="1" id="step_node_1">
                                            <div class="flow-step-circle">1</div>
                                            <span class="flow-step-label">Welcome</span>
                                        </li>
                                        <li class="flow-step-item" data-step="2" id="step_node_2">
                                            <div class="flow-step-circle">2</div>
                                            <span class="flow-step-label">Service</span>
                                        </li>
                                        <li class="flow-step-item" data-step="3" id="step_node_3">
                                            <div class="flow-step-circle">3</div>
                                            <span class="flow-step-label">Dentist</span>
                                        </li>
                                        <li class="flow-step-item" data-step="4" id="step_node_4">
                                            <div class="flow-step-circle">4</div>
                                            <span class="flow-step-label">Date &amp; Time</span>
                                        </li>
                                        <li class="flow-step-item" data-step="5" id="step_node_5">
                                            <div class="flow-step-circle">5</div>
                                            <span class="flow-step-label">Details</span>
                                        </li>
                                        <li class="flow-step-item" data-step="6" id="step_node_6">
                                            <div class="flow-step-circle">6</div>
                                            <span class="flow-step-label">Confirm</span>
                                        </li>
                                    </ul>
                                </div>

                                <!-- ============================================================ -->
                                <!-- STEP 1: WELCOME SCREEN (Matches User Reference Layout) -->
                                <!-- ============================================================ -->
                                <div class="flow-step-pane" id="pane_step_1">
                                    <div class="text-center py-2 mb-4">
                                        <span class="choice-badge text-info" style="background: rgba(0, 242, 254, 0.18) !important; color: #38bdf8 !important; border: 1px solid rgba(0, 242, 254, 0.35);">
                                            Online Dental Booking
                                        </span>
                                        <h1 class="flow-title">Welcome!!!</h1>
                                        <p class="flow-subtitle mx-auto" style="max-width: 580px;">
                                            To book an appointment, first let us know if you've visited before.
                                        </p>
                                    </div>

                                    <div class="row g-4 justify-content-center mb-4">
                                        <!-- New Patient Card -->
                                        <div class="col-md-6">
                                            <div class="choice-card-welcome" id="card_choose_new" onclick="selectPatientType('new')">
                                                <div class="choice-icon-wrap choice-icon-new">
                                                    <i class="fa fa-user-plus"></i>
                                                </div>
                                                <div>
                                                    <span class="choice-badge text-info" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35);">First Visit</span>
                                                </div>
                                                <h3 class="fw-bold text-white mb-2" style="font-size: 1.45rem;">New Patient</h3>
                                                <p class="mb-4">
                                                    First time visiting our dental practice? Register easily in under two minutes and choose your preferred dentist.
                                                </p>
                                                <button type="button" class="btn btn-outline-info w-100 py-2 fw-semibold rounded-pill" style="border-color: #38bdf8; color: #38bdf8; background: rgba(56, 189, 248, 0.08);">
                                                    I am a New Patient <i class="fa fa-arrow-right ms-2"></i>
                                                </button>
                                            </div>
                                        </div>

                                        <!-- Returning Patient Card -->
                                        <div class="col-md-6">
                                            <div class="choice-card-welcome" id="card_choose_returning" onclick="selectPatientType('returning')">
                                                <div class="choice-icon-wrap choice-icon-returning">
                                                    <i class="fa fa-id-card-o"></i>
                                                </div>
                                                <div>
                                                    <span class="choice-badge text-warning" style="background: rgba(139, 92, 246, 0.2); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.35);">Existing Record</span>
                                                </div>
                                                <h3 class="fw-bold text-white mb-2" style="font-size: 1.45rem;">Returning Patient</h3>
                                                <p class="mb-4">
                                                    Visited our clinic before? Fast-track booking using your registered mobile number or Patient ID without duplicate forms.
                                                </p>
                                                <button type="button" class="btn btn-outline-warning w-100 py-2 fw-semibold rounded-pill" style="border-color: #c084fc; color: #c084fc; background: rgba(139, 92, 246, 0.08);">
                                                    I am a Returning Patient <i class="fa fa-arrow-right ms-2"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- ============================================================ -->
                                <!-- STEP 2: CHOOSE APPOINTMENT TYPE -->
                                <!-- ============================================================ -->
                                <div class="flow-step-pane d-none" id="pane_step_2">
                                    <div class="d-flex align-items-center justify-content-between mb-4">
                                        <div>
                                            <h2 class="flow-title mb-1">Choose Appointment Type</h2>
                                            <p class="flow-subtitle mb-0">Select the treatment or examination service you require.</p>
                                        </div>
                                        <span class="badge rounded-pill px-3 py-2" id="badge_patient_type" style="background: rgba(0, 242, 254, 0.18); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.4); font-size: 0.85rem;">
                                            New Patient
                                        </span>
                                    </div>

                                    <div class="row g-3 mb-4" id="appointment_types_grid">
                                        <t t-foreach="all_types" t-as="atype">
                                            <t t-set="meta" t-value="type_meta.get(atype.id, {'dur': 30, 'price': 0, 'icon': 'fa-stethoscope', 'desc': 'Specialist dental consultation and clinical assessment.'})"/>
                                            <div class="col-md-6 col-lg-4">
                                                <div class="selectable-card type-card" t-att-data-type-id="atype.id" t-att-data-type-name="atype.name" t-att-data-duration="meta['dur']" t-att-data-price="meta['price']" onclick="selectAppointmentType(this)">
                                                    <div class="card-check-indicator"><i class="fa fa-check" style="font-size: 0.75rem;"></i></div>
                                                    <div class="d-flex align-items-center mb-2">
                                                        <div class="rounded-3 p-2 me-3" style="background: rgba(56, 189, 248, 0.18); color: #38bdf8;">
                                                            <i t-attf-class="fa #{meta['icon']} fs-5"></i>
                                                        </div>
                                                        <div>
                                                            <h5 class="fw-bold text-white mb-0" style="font-size: 1.05rem;"><t t-esc="atype.name"/></h5>
                                                        </div>
                                                    </div>
                                                    <p class="small mb-3" style="color: #cbd5e1; line-height: 1.45; min-height: 40px;">
                                                        <t t-esc="meta['desc']"/>
                                                    </p>
                                                    <div class="d-flex align-items-center justify-content-between pt-2 border-top" style="border-color: rgba(255, 255, 255, 0.1) !important;">
                                                        <span class="card-meta-pill">
                                                            <i class="fa fa-clock-o me-1"></i><t t-esc="meta['dur']"/> mins
                                                        </span>
                                                        <t t-if="meta['price'] &gt; 0">
                                                            <span class="fw-bold" style="color: #38bdf8; font-size: 0.95rem;">$<t t-esc="meta['price']"/></span>
                                                        </t>
                                                    </div>
                                                </div>
                                            </div>
                                        </t>
                                    </div>

                                    <div class="d-flex justify-content-between align-items-center pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.1) !important;">
                                        <button type="button" class="flow-btn-secondary" onclick="goToStep(1)">
                                            <i class="fa fa-arrow-left me-2"></i> Back
                                        </button>
                                        <button type="button" class="flow-btn-primary" id="btn_step_2_next" onclick="goToStep(3)" disabled="disabled">
                                            Continue to Dentist <i class="fa fa-arrow-right ms-2"></i>
                                        </button>
                                    </div>
                                </div>

                                <!-- ============================================================ -->
                                <!-- STEP 3: CHOOSE YOUR DENTIST -->
                                <!-- ============================================================ -->
                                <div class="flow-step-pane d-none" id="pane_step_3">
                                    <div class="mb-4">
                                        <h2 class="flow-title mb-1">Choose Your Dentist</h2>
                                        <p class="flow-subtitle mb-0">Select your preferred dental surgeon or choose Any Available Doctor for earliest appointments.</p>
                                    </div>

                                    <div class="row g-3 mb-4" id="dentists_grid">
                                        <!-- Option: Any Dentist -->
                                        <div class="col-md-4">
                                            <div class="selectable-card dentist-card selected" data-doctor-id="any" data-doctor-name="Any Available Specialist" data-doctor-spec="Next Available Specialist" onclick="selectDentist(this)">
                                                <div class="card-check-indicator"><i class="fa fa-check" style="font-size: 0.75rem;"></i></div>
                                                <div class="d-flex align-items-center mb-3">
                                                    <div class="rounded-circle p-3 me-3" style="background: rgba(0, 242, 254, 0.18); color: #00f2fe; width: 54px; height: 54px; display: flex; align-items: center; justify-content: center;">
                                                        <i class="fa fa-users fs-4"></i>
                                                    </div>
                                                    <div>
                                                        <h5 class="fw-bold text-white mb-0" style="font-size: 1.1rem;">Any Dentist</h5>
                                                        <span class="small" style="color: #38bdf8; font-weight: 500;">Earliest Opening</span>
                                                    </div>
                                                </div>
                                                <p class="small mb-2" style="color: #cbd5e1; line-height: 1.45;">
                                                    Maximum availability. Automatically assigns the first qualified dental surgeon free at your chosen time.
                                                </p>
                                                <span class="badge rounded-pill bg-success-subtle text-success small px-2 py-1">Fastest Booking</span>
                                            </div>
                                        </div>

                                        <!-- Configured Dentists from Odoo -->
                                        <t t-foreach="all_dentists" t-as="doc">
                                            <div class="col-md-4">
                                                <div class="selectable-card dentist-card" t-att-data-doctor-id="doc.id" t-att-data-doctor-name="doc.name" t-att-data-doctor-spec="doc.specialization or 'Dental Surgeon'" onclick="selectDentist(this)">
                                                    <div class="card-check-indicator"><i class="fa fa-check" style="font-size: 0.75rem;"></i></div>
                                                    <div class="d-flex align-items-center mb-3">
                                                        <div class="rounded-circle p-3 me-3" style="background: rgba(139, 92, 246, 0.18); color: #c084fc; width: 54px; height: 54px; display: flex; align-items: center; justify-content: center;">
                                                            <i class="fa fa-user-md fs-4"></i>
                                                        </div>
                                                        <div>
                                                            <h5 class="fw-bold text-white mb-0" style="font-size: 1.1rem;"><t t-esc="doc.name"/></h5>
                                                            <span class="small" style="color: #38bdf8; font-weight: 500;"><t t-esc="doc.specialization or 'Dental Surgeon'"/></span>
                                                        </div>
                                                    </div>
                                                    <p class="small mb-2" style="color: #cbd5e1; line-height: 1.45;">
                                                        Dedicated consultation, comprehensive smile planning &amp; treatment care.
                                                    </p>
                                                    <span class="badge rounded-pill bg-info-subtle text-info small px-2 py-1">
                                                        <i class="fa fa-check-circle me-1"></i>Verified Doctor
                                                    </span>
                                                </div>
                                            </div>
                                        </t>
                                    </div>

                                    <div class="d-flex justify-content-between align-items-center pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.1) !important;">
                                        <button type="button" class="flow-btn-secondary" onclick="goToStep(2)">
                                            <i class="fa fa-arrow-left me-2"></i> Back
                                        </button>
                                        <button type="button" class="flow-btn-primary" id="btn_step_3_next" onclick="goToStep(4)">
                                            Continue to Date &amp; Time <i class="fa fa-arrow-right ms-2"></i>
                                        </button>
                                    </div>
                                </div>

                                <!-- ============================================================ -->
                                <!-- STEP 4: SELECT DATE AND TIME (Interactive Calendar + Live Slots) -->
                                <!-- ============================================================ -->
                                <div class="flow-step-pane d-none" id="pane_step_4">
                                    <div class="mb-4">
                                        <h2 class="flow-title mb-1">Select Date &amp; Time</h2>
                                        <p class="flow-subtitle mb-0">Choose an available clinic day and live validated time slot.</p>
                                    </div>

                                    <div class="row g-4 mb-4">
                                        <!-- Left Column: Interactive Calendar -->
                                        <div class="col-lg-6">
                                            <div class="calendar-container">
                                                <div class="calendar-header">
                                                    <button type="button" class="calendar-nav-btn" onclick="prevMonth()">
                                                        <i class="fa fa-chevron-left"></i>
                                                    </button>
                                                    <h4 class="fw-bold text-white mb-0" id="cal_month_year">October 2026</h4>
                                                    <button type="button" class="calendar-nav-btn" onclick="nextMonth()">
                                                        <i class="fa fa-chevron-right"></i>
                                                    </button>
                                                </div>

                                                <div class="calendar-weekdays">
                                                    <div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div><div>Sun</div>
                                                </div>

                                                <div class="calendar-days-grid" id="cal_days_grid">
                                                    <!-- Generated dynamically via JS -->
                                                </div>

                                                <div class="d-flex align-items-center justify-content-center gap-3 mt-3 pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.1) !important; font-size: 0.82rem; color: #cbd5e1;">
                                                    <span class="d-flex align-items-center"><span class="cal-dot me-1"></span> Available</span>
                                                    <span class="d-flex align-items-center"><span style="width: 8px; height: 8px; border-radius: 50%; background: #00f2fe; display: inline-block;" class="me-1"></span> Selected</span>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Right Column: Live Available Slots -->
                                        <div class="col-lg-6">
                                            <div class="slots-container">
                                                <div class="d-flex align-items-center justify-content-between mb-3">
                                                    <div>
                                                        <h5 class="fw-bold text-white mb-0" id="slots_header_date">Available Slots</h5>
                                                        <span class="small" id="slots_doctor_label" style="color: #38bdf8; font-weight: 500;">For Any Available Specialist</span>
                                                    </div>
                                                    <span class="badge rounded-pill bg-primary" id="slots_count_badge" style="background: rgba(0, 242, 254, 0.25) !important; color: #00f2fe; font-size: 0.82rem;">
                                                        Loading...
                                                    </span>
                                                </div>

                                                <div id="slots_loading_spinner" class="text-center py-5">
                                                    <i class="fa fa-spinner fa-spin fa-2x" style="color: #00f2fe;"></i>
                                                    <p class="small mt-2 mb-0" style="color: #cbd5e1;">Checking doctor availability...</p>
                                                </div>

                                                <div id="slots_content_area" class="d-none">
                                                    <!-- Morning Slots -->
                                                    <div class="mb-3">
                                                        <div class="slot-period-title">
                                                            <i class="fa fa-sun-o me-2 text-warning"></i> Morning Sessions (09:00 AM - 01:00 PM)
                                                        </div>
                                                        <div class="row g-2" id="grid_morning_slots"></div>
                                                    </div>

                                                    <!-- Afternoon Slots -->
                                                    <div>
                                                        <div class="slot-period-title">
                                                            <i class="fa fa-moon-o me-2 text-info"></i> Afternoon Sessions (02:00 PM - 06:00 PM)
                                                        </div>
                                                        <div class="row g-2" id="grid_afternoon_slots"></div>
                                                    </div>
                                                </div>

                                                <div id="slots_empty_message" class="d-none text-center py-4">
                                                    <i class="fa fa-calendar-times-o fa-2x text-muted mb-2"></i>
                                                    <p class="small mb-0" style="color: #cbd5e1;">No open appointments on this date. Please select another date.</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="d-flex justify-content-between align-items-center pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.1) !important;">
                                        <button type="button" class="flow-btn-secondary" onclick="goToStep(3)">
                                            <i class="fa fa-arrow-left me-2"></i> Back
                                        </button>
                                        <button type="button" class="flow-btn-primary" id="btn_step_4_next" onclick="goToStep(5)" disabled="disabled">
                                            Continue to Details <i class="fa fa-arrow-right ms-2"></i>
                                        </button>
                                    </div>
                                </div>

                                <!-- ============================================================ -->
                                <!-- STEP 5: PATIENT DETAILS (New vs Returning Patient Handling) -->
                                <!-- ============================================================ -->
                                <div class="flow-step-pane d-none" id="pane_step_5">
                                    <div class="mb-4">
                                        <h2 class="flow-title mb-1" id="details_title">Patient Information</h2>
                                        <p class="flow-subtitle mb-0" id="details_subtitle">Please provide your contact details for appointment confirmation.</p>
                                    </div>

                                    <!-- RETURNING PATIENT SECTION -->
                                    <div id="returning_lookup_box" class="d-none mb-4">
                                        <div class="review-card-box p-4" style="border: 1.5px solid rgba(139, 92, 246, 0.45); background: rgba(22, 28, 65, 0.85);">
                                            <label class="flow-input-label text-warning fs-6 mb-2">
                                                <i class="fa fa-search me-2"></i>Look Up Your Patient Profile
                                            </label>
                                            <p class="small mb-3" style="color: #cbd5e1;">
                                                Enter your registered mobile number, email, or Patient ID (e.g. 9061886693 or PT-00001).
                                            </p>
                                            <div class="input-group">
                                                <input type="text" id="ret_identifier_input" class="flow-input rounded-start-3" placeholder="e.g. 9061886693 or nimyathomas@gmail.com"/>
                                                <button type="button" class="btn btn-warning px-4 fw-bold rounded-end-3" onclick="searchReturningPatient()" id="btn_search_ret">
                                                    <i class="fa fa-search me-1"></i> Search
                                                </button>
                                            </div>
                                            <div id="ret_search_alert" class="alert d-none mt-3 py-2 small mb-0"></div>
                                        </div>

                                        <!-- Verified Patient Badge -->
                                        <div id="verified_patient_card" class="d-none alert alert-success rounded-3 p-3 mb-4" style="background: rgba(16, 185, 129, 0.18); border: 1.5px solid #10b981; color: #f8fafc;">
                                            <div class="d-flex align-items-center justify-content-between">
                                                <div>
                                                    <div class="fw-bold text-success fs-5">
                                                        <i class="fa fa-check-circle me-2"></i><span id="verified_name">Patient Name</span>
                                                    </div>
                                                    <div class="small mt-1" style="color: #e2e8f0;">
                                                        Patient ID: <strong class="text-white" id="verified_id">PT-00000</strong> &amp;bull; Phone: <strong class="text-white" id="verified_phone">-</strong>
                                                    </div>
                                                </div>
                                                <button type="button" class="btn btn-sm btn-outline-light rounded-pill" onclick="resetReturningSearch()">
                                                    Change
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- NEW PATIENT FORM FIELDS -->
                                    <form id="form_patient_details" novalidate="novalidate">
                                        <div id="new_patient_fields">
                                            <div class="row g-3 mb-3">
                                                <div class="col-md-6">
                                                    <label class="flow-input-label">Full Name <span class="text-danger">*</span></label>
                                                    <input type="text" class="flow-input" id="inp_name" name="name" placeholder="e.g. Sarah Connor" required="required"/>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="flow-input-label">Mobile Phone Number <span class="text-danger">*</span></label>
                                                    <input type="tel" class="flow-input" id="inp_phone" name="phone" placeholder="e.g. 9876543210" required="required"/>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="flow-input-label">Email Address <span class="text-danger">*</span></label>
                                                    <input type="email" class="flow-input" id="inp_email" name="email" placeholder="e.g. sarah@example.com" required="required"/>
                                                </div>
                                                <div class="col-md-3 col-6">
                                                    <label class="flow-input-label">Date of Birth</label>
                                                    <input type="date" class="flow-input" id="inp_dob" name="dob"/>
                                                </div>
                                                <div class="col-md-3 col-6">
                                                    <label class="flow-input-label">Gender</label>
                                                    <select class="flow-input" id="inp_gender" name="gender">
                                                        <option value="">Select...</option>
                                                        <option value="female">Female</option>
                                                        <option value="male">Male</option>
                                                        <option value="other">Other</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Notes Field (Both New and Returning) -->
                                        <div class="mb-3">
                                            <label class="flow-input-label">Reason for Visit / Appointment Notes (Optional)</label>
                                            <textarea class="flow-input" id="inp_notes" name="notes" rows="2" placeholder="e.g. routine scaling, tooth pain on upper molar, cosmetic evaluation"></textarea>
                                        </div>

                                        <!-- Confidentiality Notice -->
                                        <div class="privacy-notice-box">
                                            <i class="fa fa-shield fa-2x me-3 text-warning"></i>
                                            <div>
                                                <strong class="text-white d-block mb-1">Healthcare Data Privacy Notice:</strong>
                                                Please do not enter confidential diagnostic details, medical charts, or prescription specifics in this public form. Your medical assessment takes place in private clinical confidence with your doctor.
                                            </div>
                                        </div>
                                    </form>

                                    <div class="d-flex justify-content-between align-items-center pt-4 border-top mt-4" style="border-color: rgba(255, 255, 255, 0.1) !important;">
                                        <button type="button" class="flow-btn-secondary" onclick="goToStep(4)">
                                            <i class="fa fa-arrow-left me-2"></i> Back
                                        </button>
                                        <button type="button" class="flow-btn-primary" id="btn_step_5_next" onclick="validateStep5()">
                                            Review &amp; Confirm <i class="fa fa-arrow-right ms-2"></i>
                                        </button>
                                    </div>
                                </div>

                                <!-- ============================================================ -->
                                <!-- STEP 6: REVIEW AND CONFIRM -->
                                <!-- ============================================================ -->
                                <div class="flow-step-pane d-none" id="pane_step_6">
                                    <div class="mb-4">
                                        <h2 class="flow-title mb-1">Review &amp; Confirm</h2>
                                        <p class="flow-subtitle mb-0">Please verify your booking summary before final confirmation.</p>
                                    </div>

                                    <div class="review-card-box">
                                        <!-- Patient Info -->
                                        <div class="review-row">
                                            <div class="review-label">
                                                <i class="fa fa-user me-2 text-primary"></i> Patient
                                            </div>
                                            <div class="review-value">
                                                <span id="rev_patient_name">-</span>
                                                <span class="badge bg-secondary ms-1" id="rev_patient_badge">New</span>
                                                <a class="review-edit-link" onclick="goToStep(5)">(Edit)</a>
                                            </div>
                                        </div>

                                        <!-- Contact Info -->
                                        <div class="review-row">
                                            <div class="review-label">
                                                <i class="fa fa-phone me-2 text-primary"></i> Contact
                                            </div>
                                            <div class="review-value">
                                                <span id="rev_patient_contact">-</span>
                                            </div>
                                        </div>

                                        <!-- Service -->
                                        <div class="review-row">
                                            <div class="review-label">
                                                <i class="fa fa-stethoscope me-2 text-info"></i> Service
                                            </div>
                                            <div class="review-value">
                                                <span id="rev_service_name">-</span>
                                                <span class="small ms-1" style="color: #cbd5e1;" id="rev_service_meta"></span>
                                                <a class="review-edit-link" onclick="goToStep(2)">(Edit)</a>
                                            </div>
                                        </div>

                                        <!-- Dentist -->
                                        <div class="review-row">
                                            <div class="review-label">
                                                <i class="fa fa-user-md me-2 text-warning"></i> Dentist
                                            </div>
                                            <div class="review-value">
                                                <span id="rev_doctor_name">-</span>
                                                <a class="review-edit-link" onclick="goToStep(3)">(Edit)</a>
                                            </div>
                                        </div>

                                        <!-- Scheduled Date and Time -->
                                        <div class="review-row">
                                            <div class="review-label">
                                                <i class="fa fa-calendar-check-o me-2 text-success"></i> Date &amp; Time
                                            </div>
                                            <div class="review-value" style="color: #00f2fe; font-size: 1.05rem;">
                                                <span id="rev_datetime">-</span>
                                                <a class="review-edit-link" onclick="goToStep(4)">(Edit)</a>
                                            </div>
                                        </div>

                                        <!-- Notes -->
                                        <div class="review-row" id="rev_notes_row">
                                            <div class="review-label">
                                                <i class="fa fa-commenting-o me-2 text-secondary"></i> Notes
                                            </div>
                                            <div class="review-value" style="color: #cbd5e1;" id="rev_notes_text">
                                                None
                                            </div>
                                        </div>
                                    </div>

                                    <div id="booking_submit_alert" class="alert alert-danger d-none mb-3"></div>

                                    <div class="d-flex justify-content-between align-items-center pt-3 border-top" style="border-color: rgba(255, 255, 255, 0.1) !important;">
                                        <button type="button" class="flow-btn-secondary" onclick="goToStep(5)">
                                            <i class="fa fa-arrow-left me-2"></i> Back to Edit
                                        </button>
                                        <button type="button" class="flow-btn-primary px-5 py-3 fs-5" id="btn_confirm_booking" onclick="submitFinalBooking()">
                                            <i class="fa fa-calendar-plus-o me-2"></i> Confirm Booking
                                        </button>
                                    </div>
                                </div>

                                <!-- ============================================================ -->
                                <!-- STEP 7: CONFIRMATION SCREEN (Success State) -->
                                <!-- ============================================================ -->
                                <div class="flow-step-pane d-none text-center py-4" id="pane_step_success">
                                    <div class="success-pulse-icon">
                                        <i class="fa fa-check"></i>
                                    </div>
                                    <span class="badge rounded-pill bg-success-subtle text-success px-3 py-2 mb-2" style="font-size: 0.85rem;">
                                        Booking Confirmed
                                    </span>
                                    <h1 class="flow-title mb-2">Appointment Scheduled!</h1>
                                    <p class="flow-subtitle mx-auto mb-4" style="max-width: 550px;">
                                        Your dental appointment request is confirmed in our clinic system. Our reception desk looks forward to welcoming you.
                                    </p>

                                    <!-- Success Details Box -->
                                    <div class="review-card-box mx-auto text-start p-4 mb-4" style="max-width: 580px; border-color: rgba(0, 242, 254, 0.35);">
                                        <div class="d-flex align-items-center justify-content-between pb-3 mb-3 border-bottom" style="border-color: rgba(255, 255, 255, 0.12) !important;">
                                            <span class="small" style="color: #cbd5e1;">Appointment Reference</span>
                                            <span class="badge bg-primary px-3 py-2 fs-6" id="success_ref">APT/2026/00000</span>
                                        </div>
                                        <div class="row g-2 small">
                                            <div class="col-4" style="color: #cbd5e1;">Patient:</div>
                                            <div class="col-8 fw-bold text-white" id="success_patient">-</div>

                                            <div class="col-4" style="color: #cbd5e1;">Dentist:</div>
                                            <div class="col-8 fw-bold text-white" id="success_doctor">-</div>

                                            <div class="col-4" style="color: #cbd5e1;">Service:</div>
                                            <div class="col-8 fw-bold text-white" id="success_service">-</div>

                                            <div class="col-4" style="color: #cbd5e1;">Scheduled:</div>
                                            <div class="col-8 fw-bold" style="color: #00f2fe;" id="success_datetime">-</div>

                                            <div class="col-4" style="color: #cbd5e1;">Status:</div>
                                            <div class="col-8 fw-bold text-warning" id="success_status">Pending Confirmation</div>
                                        </div>
                                    </div>

                                    <div class="d-flex flex-wrap justify-content-center gap-3">
                                        <button type="button" class="flow-btn-secondary" onclick="restartBooking()">
                                            <i class="fa fa-plus-circle me-2"></i> Book Another Appointment
                                        </button>
                                        <a href="/" class="flow-btn-primary text-decoration-none">
                                            <i class="fa fa-home me-2"></i> Return to Homepage
                                        </a>
                                    </div>
                                </div>

                            </div> <!-- /dental-flow-card -->

                        </div>
                    </div>
                </div>
            </section>

            <!-- INTERACTIVE JAVASCRIPT CONTROLLER -->
            <script type="text/javascript">
            // Global Booking State
            var bookingState = {
                currentStep: 1,
                patientType: 'new', // 'new' or 'returning'
                returningPatientId: null,
                returningPatientData: null,
                appointmentTypeId: null,
                appointmentTypeName: '',
                duration: 30,
                price: 0,
                doctorId: 'any',
                doctorName: 'Any Available Specialist',
                selectedDate: '',
                selectedDateFormatted: '',
                selectedTime: '',
                selectedTimeFormatted: '',
                notes: '',
                name: '',
                phone: '',
                email: '',
                dob: '',
                gender: '',
                currentCalYear: 2026,
                currentCalMonth: 9 // 0-indexed (9 = October)
            };

            function getCsrfToken() {
                var el = document.querySelector('input[name="csrf_token"]');
                if (el &amp;&amp; el.value) return el.value;
                if (window.odoo &amp;&amp; window.odoo.csrf_token) return window.odoo.csrf_token;
                return '';
            }

            function updateProgressBar() {
                var totalSteps = 6;
                var pct = ((bookingState.currentStep - 1) / (totalSteps - 1)) * 100;
                document.getElementById('progress_fill').style.width = pct + '%';

                for (var i = 1; i &lt;= totalSteps; i++) {
                    var node = document.getElementById('step_node_' + i);
                    if (!node) continue;
                    node.classList.remove('active', 'completed');
                    if (i === bookingState.currentStep) {
                        node.classList.add('active');
                    } else if (i &lt; bookingState.currentStep) {
                        node.classList.add('completed');
                        node.onclick = (function(stepNum) {
                            return function() { goToStep(stepNum); };
                        })(i);
                    } else {
                        node.onclick = null;
                    }
                }
            }

            function goToStep(stepNumber) {
                // Hide all panes
                for (var s = 1; s &lt;= 6; s++) {
                    var p = document.getElementById('pane_step_' + s);
                    if (p) p.classList.add('d-none');
                }
                var pSuccess = document.getElementById('pane_step_success');
                if (pSuccess) pSuccess.classList.add('d-none');

                var targetPane = document.getElementById('pane_step_' + stepNumber);
                if (targetPane) {
                    targetPane.classList.remove('d-none');
                    bookingState.currentStep = stepNumber;
                    updateProgressBar();

                    // Only scroll smoothly if the top of the appointment card has scrolled out of view above the screen
                    var card = document.getElementById('dental_flow_card');
                    if (card) {
                        var rect = card.getBoundingClientRect();
                        if (rect.top &lt; 0) {
                            card.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                }

                // Step-specific initializers
                if (stepNumber === 4) {
                    renderCalendar();
                    if (!bookingState.selectedDate) {
                        // Default to tomorrow
                        var tmr = new Date();
                        tmr.setDate(tmr.getDate() + 1);
                        selectCalendarDate(tmr.getFullYear(), tmr.getMonth(), tmr.getDate());
                    } else {
                        fetchSlotsForDate(bookingState.selectedDate);
                    }
                } else if (stepNumber === 5) {
                    setupStep5Details();
                } else if (stepNumber === 6) {
                    populateReviewSummary();
                }
            }

            // Step 1: Select Patient Type
            function selectPatientType(type) {
                bookingState.patientType = type;
                var badge = document.getElementById('badge_patient_type');
                if (badge) {
                    badge.textContent = type === 'new' ? 'New Patient' : 'Returning Patient';
                }
                goToStep(2);
            }

            // Step 2: Select Appointment Type
            function selectAppointmentType(cardEl) {
                document.querySelectorAll('.type-card').forEach(function(c) { c.classList.remove('selected'); });
                cardEl.classList.add('selected');

                bookingState.appointmentTypeId = cardEl.getAttribute('data-type-id');
                bookingState.appointmentTypeName = cardEl.getAttribute('data-type-name');
                bookingState.duration = parseFloat(cardEl.getAttribute('data-duration') || 30);
                bookingState.price = parseFloat(cardEl.getAttribute('data-price') || 0);

                var nextBtn = document.getElementById('btn_step_2_next');
                if (nextBtn) nextBtn.disabled = false;
            }

            // Step 3: Select Dentist
            function selectDentist(cardEl) {
                document.querySelectorAll('.dentist-card').forEach(function(c) { c.classList.remove('selected'); });
                cardEl.classList.add('selected');

                bookingState.doctorId = cardEl.getAttribute('data-doctor-id');
                bookingState.doctorName = cardEl.getAttribute('data-doctor-name');

                var nextBtn = document.getElementById('btn_step_3_next');
                if (nextBtn) nextBtn.disabled = false;
            }

            // Step 4: Interactive Calendar and Live Slots
            function renderCalendar() {
                var monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
                var year = bookingState.currentCalYear;
                var month = bookingState.currentCalMonth;

                document.getElementById('cal_month_year').textContent = monthNames[month] + " " + year;

                var firstDayIndex = new Date(year, month, 1).getDay(); // 0 = Sun
                var adjustedFirstDay = (firstDayIndex === 0) ? 6 : firstDayIndex - 1; // Mon = 0
                var daysInMonth = new Date(year, month + 1, 0).getDate();

                var grid = document.getElementById('cal_days_grid');
                grid.innerHTML = '';

                var today = new Date();
                today.setHours(0,0,0,0);

                // Blank days before first day
                for (var b = 0; b &lt; adjustedFirstDay; b++) {
                    var blank = document.createElement('div');
                    blank.className = 'cal-day-cell disabled';
                    grid.appendChild(blank);
                }

                // Days of month
                for (var d = 1; d &lt;= daysInMonth; d++) {
                    var cell = document.createElement('div');
                    cell.className = 'cal-day-cell';
                    cell.textContent = d;

                    var cellDate = new Date(year, month, d);
                    var yyyy = year;
                    var mm = String(month + 1).padStart(2, '0');
                    var dd = String(d).padStart(2, '0');
                    var isoDate = yyyy + '-' + mm + '-' + dd;
                    cell.setAttribute('data-date', isoDate);

                    if (cellDate &lt; today) {
                        cell.classList.add('disabled');
                    } else {
                        if (cellDate.getTime() === today.getTime()) {
                            cell.classList.add('today');
                        }
                        if (bookingState.selectedDate === isoDate) {
                            cell.classList.add('selected');
                        }
                        (function(y, m, dayVal, iso) {
                            cell.onclick = function() {
                                selectCalendarDate(y, m, dayVal);
                            };
                        })(year, month, d, isoDate);
                    }
                    grid.appendChild(cell);
                }
            }

            function prevMonth() {
                bookingState.currentCalMonth--;
                if (bookingState.currentCalMonth &lt; 0) {
                    bookingState.currentCalMonth = 11;
                    bookingState.currentCalYear--;
                }
                renderCalendar();
            }

            function nextMonth() {
                bookingState.currentCalMonth++;
                if (bookingState.currentCalMonth &gt; 11) {
                    bookingState.currentCalMonth = 0;
                    bookingState.currentCalYear++;
                }
                renderCalendar();
            }

            function selectCalendarDate(year, month, day) {
                var yyyy = year;
                var mm = String(month + 1).padStart(2, '0');
                var dd = String(day).padStart(2, '0');
                var iso = yyyy + '-' + mm + '-' + dd;

                bookingState.selectedDate = iso;
                var dObj = new Date(year, month, day);
                var options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
                bookingState.selectedDateFormatted = dObj.toLocaleDateString('en-US', options);

                // Highlight cell in calendar
                document.querySelectorAll('.cal-day-cell').forEach(function(c) {
                    c.classList.remove('selected');
                    if (c.getAttribute('data-date') === iso) {
                        c.classList.add('selected');
                    }
                });

                fetchSlotsForDate(iso);
            }

            function fetchSlotsForDate(dateStr) {
                var headerEl = document.getElementById('slots_header_date');
                var countEl = document.getElementById('slots_count_badge');
                var spinnerEl = document.getElementById('slots_loading_spinner');
                var contentEl = document.getElementById('slots_content_area');
                var emptyEl = document.getElementById('slots_empty_message');
                var docLabel = document.getElementById('slots_doctor_label');

                headerEl.textContent = bookingState.selectedDateFormatted || dateStr;
                docLabel.textContent = "For " + bookingState.doctorName;
                countEl.textContent = 'Loading...';

                spinnerEl.classList.remove('d-none');
                contentEl.classList.add('d-none');
                emptyEl.classList.add('d-none');

                var nextBtn = document.getElementById('btn_step_4_next');
                nextBtn.disabled = true;

                // Call JSON-RPC live slot endpoint
                var payload = {
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        date_str: dateStr,
                        doctor_id: bookingState.doctorId,
                        duration_minutes: bookingState.duration
                    }
                };

                fetch('/dental/get_slots', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(payload)
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    spinnerEl.classList.add('d-none');
                    var res = data.result || {};
                    var morning = res.morning_slots || [];
                    var afternoon = res.afternoon_slots || [];
                    var total = morning.length + afternoon.length;

                    countEl.textContent = total + ' slots available';

                    if (total === 0) {
                        emptyEl.classList.remove('d-none');
                        return;
                    }

                    contentEl.classList.remove('d-none');
                    renderSlotsGrid('grid_morning_slots', morning);
                    renderSlotsGrid('grid_afternoon_slots', afternoon);
                })
                .catch(function(err) {
                    spinnerEl.classList.add('d-none');
                    // Fallback to client-generated standard clinic slots if network offline
                    var fallbackMorning = [
                        { time: '09:00', label: '09:00 AM' },
                        { time: '09:45', label: '09:45 AM' },
                        { time: '10:30', label: '10:30 AM' },
                        { time: '11:15', label: '11:15 AM' },
                        { time: '12:00', label: '12:00 PM' }
                    ];
                    var fallbackAfternoon = [
                        { time: '14:00', label: '02:00 PM' },
                        { time: '14:45', label: '02:45 PM' },
                        { time: '15:30', label: '03:30 PM' },
                        { time: '16:15', label: '04:15 PM' },
                        { time: '17:00', label: '05:00 PM' }
                    ];
                    countEl.textContent = '10 slots available';
                    contentEl.classList.remove('d-none');
                    renderSlotsGrid('grid_morning_slots', fallbackMorning);
                    renderSlotsGrid('grid_afternoon_slots', fallbackAfternoon);
                });
            }

            function renderSlotsGrid(containerId, slots) {
                var container = document.getElementById(containerId);
                container.innerHTML = '';
                if (!slots || slots.length === 0) {
                    container.innerHTML = '&lt;div class="col-12" style="color: #cbd5e1; font-size: 0.82rem;"&gt;No available slots in this session&lt;/div&gt;';
                    return;
                }

                slots.forEach(function(s) {
                    var col = document.createElement('div');
                    col.className = 'col-6 col-sm-4';

                    var btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'slot-btn';
                    btn.textContent = s.label || s.time;
                    btn.setAttribute('data-time', s.time);
                    btn.setAttribute('data-label', s.label || s.time);

                    if (bookingState.selectedTime === s.time) {
                        btn.classList.add('selected');
                    }

                    btn.onclick = function() {
                        document.querySelectorAll('.slot-btn').forEach(function(b) { b.classList.remove('selected'); });
                        btn.classList.add('selected');
                        bookingState.selectedTime = s.time;
                        bookingState.selectedTimeFormatted = s.label || s.time;
                        document.getElementById('btn_step_4_next').disabled = false;
                    };

                    col.appendChild(btn);
                    container.appendChild(col);
                });
            }

            // Step 5: Patient Details Configuration
            function setupStep5Details() {
                var retBox = document.getElementById('returning_lookup_box');
                var newFields = document.getElementById('new_patient_fields');
                var title = document.getElementById('details_title');
                var sub = document.getElementById('details_subtitle');

                if (bookingState.patientType === 'returning') {
                    retBox.classList.remove('d-none');
                    title.textContent = 'Returning Patient Verification';
                    sub.textContent = 'Enter your Patient ID, phone, or email so we can link your booking to your clinical history.';
                    if (!bookingState.returningPatientId) {
                        newFields.classList.add('d-none');
                    } else {
                        newFields.classList.remove('d-none');
                    }
                } else {
                    retBox.classList.add('d-none');
                    newFields.classList.remove('d-none');
                    title.textContent = 'New Patient Details';
                    sub.textContent = 'Please enter your contact details. A new dental health record will be created for you.';
                }
            }

            function searchReturningPatient() {
                var val = (document.getElementById('ret_identifier_input').value || '').trim();
                var alertEl = document.getElementById('ret_search_alert');
                var card = document.getElementById('verified_patient_card');
                var btn = document.getElementById('btn_search_ret');

                if (!val) {
                    alertEl.className = 'alert alert-warning mt-3 py-2 small mb-0';
                    alertEl.textContent = 'Please enter your phone number, email address, or Patient ID.';
                    alertEl.classList.remove('d-none');
                    return;
                }

                btn.disabled = true;
                btn.innerHTML = '&lt;i class="fa fa-spinner fa-spin me-1"&gt;&lt;/i&gt; Checking...';

                var payload = {
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { identifier: val }
                };

                fetch('/dental/check_patient', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(payload)
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    btn.disabled = false;
                    btn.innerHTML = '&lt;i class="fa fa-search me-1"&gt;&lt;/i&gt; Search';

                    var res = data.result || {};
                    if (res.found) {
                        alertEl.classList.add('d-none');
                        card.classList.remove('d-none');

                        document.getElementById('verified_name').textContent = res.name;
                        document.getElementById('verified_id').textContent = res.dental_patient_id || 'ID Verified';
                        document.getElementById('verified_phone').textContent = res.phone || val;

                        bookingState.returningPatientId = res.id;
                        bookingState.returningPatientData = res;

                        // Pre-fill inputs
                        document.getElementById('inp_name').value = res.name || '';
                        document.getElementById('inp_phone').value = res.phone || '';
                        document.getElementById('inp_email').value = res.email || '';

                        document.getElementById('new_patient_fields').classList.remove('d-none');
                    } else {
                        card.classList.add('d-none');
                        bookingState.returningPatientId = null;
                        bookingState.returningPatientData = null;

                        alertEl.className = 'alert alert-danger mt-3 py-2 small mb-0';
                        alertEl.innerHTML = (res.message || 'No matching record found.') +
                            ' &lt;a href="javascript:void(0)" onclick="selectPatientType(\\'new\\')" class="alert-link ms-2"&gt;Register as New Patient &amp;rarr;&lt;/a&gt;';
                        alertEl.classList.remove('d-none');
                    }
                })
                .catch(function(err) {
                    btn.disabled = false;
                    btn.innerHTML = '&lt;i class="fa fa-search me-1"&gt;&lt;/i&gt; Search';
                    alertEl.className = 'alert alert-danger mt-3 py-2 small mb-0';
                    alertEl.textContent = 'Error querying patient database: ' + err;
                    alertEl.classList.remove('d-none');
                });
            }

            function resetReturningSearch() {
                bookingState.returningPatientId = null;
                bookingState.returningPatientData = null;
                document.getElementById('verified_patient_card').classList.add('d-none');
                document.getElementById('ret_search_alert').classList.add('d-none');
                document.getElementById('ret_identifier_input').value = '';
                document.getElementById('new_patient_fields').classList.add('d-none');
            }

            function validateStep5() {
                var name = (document.getElementById('inp_name').value || '').trim();
                var phone = (document.getElementById('inp_phone').value || '').trim();
                var email = (document.getElementById('inp_email').value || '').trim();

                if (bookingState.patientType === 'returning' &amp;&amp; !bookingState.returningPatientId) {
                    var retInput = (document.getElementById('ret_identifier_input').value || '').trim();
                    if (!retInput) {
                        alert('Please look up your existing patient record or switch to "New Patient".');
                        document.getElementById('ret_identifier_input').focus();
                        return;
                    }
                    searchReturningPatient();
                    return;
                }

                if (!name) {
                    alert('Please enter your full name.');
                    document.getElementById('inp_name').focus();
                    return;
                }
                if (!phone) {
                    alert('Please enter your mobile phone number.');
                    document.getElementById('inp_phone').focus();
                    return;
                }
                if (!email) {
                    alert('Please enter your email address for appointment confirmation.');
                    document.getElementById('inp_email').focus();
                    return;
                }

                bookingState.name = name;
                bookingState.phone = phone;
                bookingState.email = email;
                bookingState.dob = document.getElementById('inp_dob').value || '';
                bookingState.gender = document.getElementById('inp_gender').value || '';
                bookingState.notes = document.getElementById('inp_notes').value || '';

                goToStep(6);
            }

            // Step 6: Populate Review Summary
            function populateReviewSummary() {
                document.getElementById('rev_patient_name').textContent = bookingState.name;
                document.getElementById('rev_patient_badge').textContent = bookingState.patientType === 'new' ? 'New Patient' : 'Returning Patient (' + (bookingState.returningPatientData ? bookingState.returningPatientData.dental_patient_id : '') + ')';
                document.getElementById('rev_patient_contact').textContent = bookingState.phone + ' • ' + bookingState.email;
                document.getElementById('rev_service_name').textContent = bookingState.appointmentTypeName;
                document.getElementById('rev_service_meta').textContent = '(' + bookingState.duration + ' mins' + (bookingState.price ? ' • $' + bookingState.price : '') + ')';
                document.getElementById('rev_doctor_name').textContent = bookingState.doctorName;
                document.getElementById('rev_datetime').textContent = bookingState.selectedDateFormatted + ' at ' + bookingState.selectedTimeFormatted;

                var notesEl = document.getElementById('rev_notes_text');
                if (bookingState.notes &amp;&amp; bookingState.notes.trim()) {
                    notesEl.textContent = bookingState.notes.trim();
                    notesEl.style.color = '#ffffff';
                } else {
                    notesEl.textContent = 'None provided';
                    notesEl.style.color = '#cbd5e1';
                }
            }

            // Final Booking Submission
            function submitFinalBooking() {
                var btn = document.getElementById('btn_confirm_booking');
                var alertEl = document.getElementById('booking_submit_alert');
                alertEl.classList.add('d-none');

                btn.disabled = true;
                btn.innerHTML = '&lt;i class="fa fa-spinner fa-spin me-2"&gt;&lt;/i&gt; Creating Appointment...';

                var payload = {
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        patient_type: bookingState.patientType,
                        patient_id: bookingState.returningPatientId,
                        name: bookingState.name,
                        phone: bookingState.phone,
                        email: bookingState.email,
                        dob: bookingState.dob,
                        gender: bookingState.gender,
                        notes: bookingState.notes,
                        appointment_type_id: bookingState.appointmentTypeId,
                        doctor_id: bookingState.doctorId,
                        date_str: bookingState.selectedDate,
                        time_str: bookingState.selectedTime,
                        duration_minutes: bookingState.duration
                    }
                };

                fetch('/dental/submit_appointment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(payload)
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    btn.disabled = false;
                    btn.innerHTML = '&lt;i class="fa fa-calendar-plus-o me-2"&gt;&lt;/i&gt; Confirm Booking';

                    var result = data.result || {};
                    if (result.success) {
                        // Populate success screen
                        document.getElementById('success_ref').textContent = result.appointment_ref;
                        document.getElementById('success_patient').textContent = result.patient_name;
                        document.getElementById('success_doctor').textContent = result.doctor_name;
                        document.getElementById('success_service').textContent = result.service_name;
                        document.getElementById('success_datetime').textContent = result.date_formatted + ' at ' + result.time_formatted;
                        document.getElementById('success_status').textContent = result.status;

                        // Hide progress bar and all panes, show success
                        document.getElementById('flow_progress_bar').classList.add('d-none');
                        for (var s = 1; s &lt;= 6; s++) {
                            document.getElementById('pane_step_' + s).classList.add('d-none');
                        }
                        document.getElementById('pane_step_success').classList.remove('d-none');

                        var flowCard = document.getElementById('dental_flow_card');
                        if (flowCard) {
                            flowCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    } else {
                        alertEl.textContent = (result &amp;&amp; result.error) ? result.error : 'Booking could not be completed. Please review your entries.';
                        alertEl.classList.remove('d-none');
                    }
                })
                .catch(function(err) {
                    btn.disabled = false;
                    btn.innerHTML = '&lt;i class="fa fa-calendar-plus-o me-2"&gt;&lt;/i&gt; Confirm Booking';
                    alertEl.textContent = 'Server communication error: ' + err;
                    alertEl.classList.remove('d-none');
                });
            }

            function restartBooking() {
                bookingState.currentStep = 1;
                bookingState.patientType = 'new';
                bookingState.returningPatientId = null;
                bookingState.returningPatientData = null;
                bookingState.selectedDate = '';
                bookingState.selectedTime = '';
                bookingState.notes = '';

                document.getElementById('flow_progress_bar').classList.remove('d-none');
                document.getElementById('form_patient_details').reset();
                resetReturningSearch();
                goToStep(1);
            }

            // Init on DOM ready
            document.addEventListener('DOMContentLoaded', function() {
                updateProgressBar();

                // Select first appointment type by default if present
                var firstType = document.querySelector('.type-card');
                if (firstType) {
                    selectAppointmentType(firstType);
                }
            });
            </script>

        </div>
    </t>
</t>"""

# 1. Update XML file
with open(r'd:\dental_addons\dental_appointment\views\website_appointment_templates.xml', 'w', encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<odoo>\n    <template id="book_appointment" name="Book Dental Appointment">\n' + template_content + '\n    </template>\n</odoo>\n')
print("1. Written website_appointment_templates.xml successfully!")

# 2. Update ir.ui.view 3258 in PostgreSQL
cur.execute("""
UPDATE ir_ui_view
SET arch_db = %s, website_id = 1, write_date = NOW()
WHERE id = 3258;
""", (json.dumps({"en_US": template_content}),))
conn.commit()
conn.close()
print("2. Updated ir_ui_view 3258 in PostgreSQL database successfully!")

# 3. Update ORM cache via XML-RPC
common = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/common')
uid = common.authenticate('DenBell', 'sijikumardevipriya@gmail.com', 'admin', {})
models = xmlrpc.client.ServerProxy('http://127.0.0.1:8069/xmlrpc/2/object')
models.execute_kw('DenBell', uid, 'admin', 'ir.ui.view', 'write', [[3258], {
    'arch_db': {'en_US': template_content},
    'website_id': 1
}])
print("3. Updated ir.ui.view 3258 and cleared ORM cache via XML-RPC successfully!")
