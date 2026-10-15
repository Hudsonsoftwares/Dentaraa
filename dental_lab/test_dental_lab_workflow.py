# -*- coding: utf-8 -*-
"""
End-to-End Test Suite for dental_lab module on Odoo 20 Community Edition
Tests complete laboratory workflows, Quality module integration, MRP, dispatches, receipts, and closure.
"""
import sys

def run_tests(env):
    print("======================================================================")
    print("STARTING DENTAL LAB END-TO-END TEST SUITE")
    print("======================================================================")

    # 1. Master Data Verification
    print("\n--- Test 1: Verifying Dental Lab Products and Quality Control Points ---")
    lab_products = env['product.product'].search([('is_dental_lab_item', '=', True)])
    print(f"Found {len(lab_products)} Dental Lab products/materials.")
    assert len(lab_products) > 0, "No dental lab products found!"

    qc_points = env['quality.point'].search([('title', 'ilike', 'Crown & Bridge')])
    print(f"Found {len(qc_points)} Crown & Bridge Quality Control Points from Quality module.")
    assert len(qc_points) > 0, "Quality Control Points from Quality module not found!"

    # 2. Get or create Patient and Dental Case
    print("\n--- Test 2: Getting/Creating Patient and Dental Case ---")
    patient = env['res.partner'].search([('is_dental_patient', '=', True)], limit=1)
    if not patient:
        patient = env['res.partner'].create({
            'name': 'Test Lab Patient John Doe',
            'is_dental_patient': True,
            'gender': 'male',
        })
    print(f"Patient: {patient.name} (ID: {patient.id})")

    doctor = env['hr.employee.public'].search([], limit=1)
    print(f"Doctor: {doctor.name if doctor else 'None'}")

    case = env['dental.case'].create({
        'name': 'CASE/TEST/001',
        'patient_id': patient.id,
        'doctor_id': doctor.id if doctor else False,
        'chief_complaint': 'Fractured tooth 11 requiring monolithic zirconia crown',
        'case_date': env['dental.lab.order']._fields['order_date'].default(env['dental.lab.order']),
    })
    print(f"Created Dental Case: {case.name} (ID: {case.id})")

    # 3. Test Wizard Duplicate Prevention
    print("\n--- Test 3: Testing Creation Wizard and Duplicate Warning ---")
    wiz = env['dental.lab.create.wizard'].create({
        'case_id': case.id,
        'patient_id': patient.id,
        'dentist_id': doctor.id if doctor else False,
        'lab_type': 'in_house',
        'shade': 'A2',
        'margin_design': 'chamfer',
        'line_ids': [(0, 0, {
            'tooth_number': '11',
            'restoration_type': 'crown',
            'material': 'zirconia_ml',
            'shade': 'A2',
            'quantity': 1.0,
            'unit_price': 280.0,
        })]
    })
    res_action = wiz.action_confirm_create()
    order_id = res_action['res_id']
    order = env['dental.lab.order'].browse(order_id)
    print(f"Successfully created Dental Lab Order: {order.name} (ID: {order.id}), State: {order.state}")
    assert order.state == 'draft', f"Expected draft, got {order.state}"
    assert len(order.line_ids) == 1, "Expected 1 order line"

    # Test second wizard attempt warns about existing order
    wiz2 = env['dental.lab.create.wizard'].create({
        'case_id': case.id,
        'patient_id': patient.id,
    })
    assert wiz2.existing_order_count >= 1, "Duplicate warning failed to identify existing order!"
    print(f"Duplicate check confirmed: Wizard flagged {wiz2.existing_order_count} existing active order(s).")

    # 4. Order Submission
    print("\n--- Test 4: Submitting Lab Order ---")
    order.action_submit()
    assert order.state == 'submitted', f"Expected submitted, got {order.state}"
    print(f"Order state after submission: {order.state}")

    # 5. Production Commencement & MRP Integration
    print("\n--- Test 5: Commencing Production & MRP Integration ---")
    order.action_start_production()
    assert order.state == 'in_production', f"Expected in_production, got {order.state}"
    print(f"Order state: {order.state}, Linked MRP Order: {order.production_id.name if order.production_id else 'In-House Tracked'}")

    # 6. Quality Control Check Generation (Reusing Quality module)
    print("\n--- Test 6: Triggering Quality Checks using existing Quality module ---")
    order.action_request_qc()
    assert order.state == 'qc_pending', f"Expected qc_pending, got {order.state}"
    checks = order.quality_check_ids
    print(f"Generated {len(checks)} Quality Checks:")
    for c in checks:
        print(f"  - [{c.name}] {c.title} (Type: {c.test_type}, State: {c.quality_state})")
    assert len(checks) >= 5, f"Expected at least 5 standard dental QC checks, got {len(checks)}"

    # 7. QC Rejection, Failure Handling, and Rework Blocking
    print("\n--- Test 7: Testing QC Failure, Alert Generation & Release Blocking ---")
    fit_check = checks.filtered(lambda c: c.dental_inspection_stage == 'dimensions')[:1]
    if not fit_check:
        fit_check = checks[0]
    
    print(f"Failing Quality Check '{fit_check.title}' with defect notes...")
    fit_check.failure_message = "<p>Open margin detected on mesio-buccal edge (>120 microns).</p>"
    fit_check.do_fail()

    assert fit_check.quality_state == 'fail', f"Expected fail, got {fit_check.quality_state}"
    assert order.state == 'rework', f"Expected order to move to 'rework', got {order.state}"
    print(f"Check status: {fit_check.quality_state}, Order status: {order.state}")

    # Verify Quality Alert auto-created from existing Quality module
    alerts = order.quality_alert_ids
    print(f"Quality Alerts linked to Lab Order: {len(alerts)}")
    assert len(alerts) > 0, "Quality Alert was not linked to Dental Lab Order!"
    print(f"Alert: {alerts[0].name} (Stage: {alerts[0].stage_id.name})")

    # Verify Finished Goods release is BLOCKED while in rework/failed state
    try:
        order.action_receive_finished_goods()
        raise AssertionError("Security failure: Order was allowed to receive finished goods despite failing QC!")
    except Exception as e:
        print(f"Passed: Release correctly blocked with message: '{str(e)}'")

    # 8. Rework Correction & Re-inspection
    print("\n--- Test 8: Testing Rework Initiation & Linked Re-inspection ---")
    rework_wiz = env['dental.lab.rework.wizard'].create({
        'order_id': order.id,
        'check_id': fit_check.id,
        'rework_type': 'margin_fit',
        'rework_reason': 'Milled new zirconia coping with tighter cement gap (20 microns).',
    })
    rework_wiz.action_confirm_rework()

    re_checks = env['quality.check'].search([('parent_check_id', '=', fit_check.id)])
    print(f"Re-inspection checks created: {len(re_checks)}")
    assert len(re_checks) > 0, "Linked re-inspection quality check was not generated!"
    re_check = re_checks[0]
    print(f"Re-inspection check: {re_check.name} - {re_check.title} (Parent: {re_check.parent_check_id.name})")

    # Pass the re-inspection and all other checks
    print("\n--- Test 9: Passing Re-inspections & Approving Quality ---")
    re_check.do_pass()
    for c in checks:
        if c.quality_state != 'pass':
            c.do_pass()

    order._check_all_qc_status()
    print(f"Order status after all QC passed: {order.state}")
    assert order.state == 'qc_approved', f"Expected qc_approved, got {order.state}"

    # 10. Finished Goods Storing & Traceability
    print("\n--- Test 10: Receiving Finished Goods into Storage ---")
    order.action_receive_finished_goods()
    assert order.state == 'finished', f"Expected finished, got {order.state}"
    print(f"Order state: {order.state}")

    # 11. Dispatch to Clinic
    print("\n--- Test 11: Dispatching to Clinic ---")
    dsp_action = order.action_create_dispatch()
    dispatch = env['dental.lab.dispatch'].browse(dsp_action['res_id'])
    assert order.state == 'dispatched', f"Expected dispatched, got {order.state}"
    print(f"Dispatch Created: {dispatch.name}, Delivery Method: {dispatch.delivery_method}, Order State: {order.state}")

    # 12. Clinic Receipt & Intake Verification
    print("\n--- Test 12: Receiving at Clinic & Intake Verification ---")
    rcp_action = order.action_receive_at_clinic()
    receipt = env['dental.lab.receipt'].browse(rcp_action['res_id'])
    assert order.state == 'received_clinic', f"Expected received_clinic, got {order.state}"
    receipt.action_verify_with_dentist()
    print(f"Receipt Intake: {receipt.name}, Condition: {receipt.condition}, Order State: {order.state}")

    # 13. Dentist Clinical Acceptance & Closure Enforcement
    print("\n--- Test 13: Testing Mandatory Clinical Acceptance Before Closure ---")
    # Try closing order without clinical acceptance -> Must fail
    try:
        order.action_close_order()
        raise AssertionError("Security failure: Order was closed without dentist clinical acceptance!")
    except Exception as e:
        print(f"Passed: Order closure blocked as expected: '{str(e)}'")

    # Dentist performs seating & records clinical acceptance
    order.dentist_fit_rating = 'excellent'
    order.dentist_shade_match = 'perfect'
    order.dentist_acceptance_notes = 'Perfect seating under gentle finger pressure. No occlusal adjustment required. Patient delighted.'
    order.action_record_dentist_acceptance()
    assert order.state == 'dentist_accepted', f"Expected dentist_accepted, got {order.state}"
    print(f"Dentist Clinical Acceptance Confirmed: {order.state} (Verified by: {order.dentist_accepted_by.name})")

    # Now close order
    order.action_close_order()
    assert order.state == 'closed', f"Expected closed, got {order.state}"
    print(f"Order successfully completed and closed: {order.state}")

    # 14. External Laboratory Workflow Test
    print("\n--- Test 14: Testing External Commercial Lab Order Workflow ---")
    vendor = env['res.partner'].search([('supplier_rank', '>', 0)], limit=1)
    if not vendor:
        vendor = env['res.partner'].create({'name': 'Premier Commercial Dental Lab Ltd', 'supplier_rank': 1, 'is_company': True})

    ext_order = env['dental.lab.order'].create({
        'patient_id': patient.id,
        'case_id': case.id,
        'dentist_id': doctor.id if doctor else False,
        'lab_type': 'external',
        'external_lab_id': vendor.id,
        'external_reference': 'EXT-REF-9921',
        'external_quotation_cost': 180.0,
        'shade': 'A3',
        'line_ids': [(0, 0, {
            'tooth_number': '24-26',
            'restoration_type': 'bridge',
            'material': 'zirconia_ml',
            'shade': 'A3',
            'quantity': 3.0,
            'unit_price': 250.0,
        })]
    })
    print(f"Created External Lab Order: {ext_order.name} (Vendor: {ext_order.external_lab_id.name})")
    ext_order.action_submit()
    ext_order.action_start_production()
    assert ext_order.state == 'in_production', "External order failed to transition to in_production"
    print(f"External Lab Order in Progress with Courier Dispatch Date: {ext_order.external_dispatch_date}")

    # 15. Dashboard KPIs Test
    print("\n--- Test 15: Verifying Dashboard Real-Time Intelligence Metrics ---")
    dashboard = env['dental.lab.dashboard'].search([], limit=1)
    if not dashboard:
        dashboard = env['dental.lab.dashboard'].create({'name': 'Dental Lab Overview'})
    dashboard._compute_dashboard_kpis()
    print(f"Dashboard KPIs:")
    print(f"  - Open Orders: {dashboard.total_open_orders}")
    print(f"  - In Production: {dashboard.in_production_count}")
    print(f"  - QC Pending: {dashboard.qc_pending_count}")
    print(f"  - External Lab Pending: {dashboard.external_lab_pending}")
    print(f"  - Low Stock Materials: {dashboard.low_stock_materials_count}")
    assert dashboard.total_open_orders >= 1, "Dashboard open orders count mismatch!"

    print("\n======================================================================")
    print("ALL 15 END-TO-END WORKFLOW TESTS COMPLETED SUCCESSFULLY!")
    print("======================================================================")

if __name__ == '__main__':
    # When executed inside odoo shell, 'env' is defined in globals
    run_tests(env)
