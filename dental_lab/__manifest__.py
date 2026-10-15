# -*- coding: utf-8 -*-
{
    'name': 'Dental Lab',
    'version': '20.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Dental Laboratory Workflow, Prosthetics Fabrication, Materials Purchasing, In-House MRP, Quality Control, Dispatch & Clinic Acceptance',
    'description': """
Dental Laboratory Management Module for Odoo 20 Community Edition
==================================================================
A complete, integrated Dental Laboratory Information & Production Management module.

Key Features:
-------------
1. **Material & Inventory Catalog**:
   - Manages dental raw materials (Zirconia discs, E.max blocks, Co-Cr alloy, Die stone, resins).
   - Artificial teeth catalog (VITA classic & 3D master shades).
   - Consumables and finished custom prosthetics (Crowns, Bridges, Dentures, Veneers, Abutments, Splints).
   - Strict tracking using native Odoo stock movements and lot/batch tracing.

2. **Purchasing & Supplier Procurement**:
   - Integrated with standard Odoo Purchase for dental materials, discs, and burs replenishment.
   - Incoming warehouse inspection and discrepancies tracking.

3. **In-House Production & MRP Manufacturing**:
   - Reuses Odoo MRP bills of materials (BOM), work centers, routing operations, and consumption.
   - Tracks technician assignments, planned turnaround time, and manufacturing orders.

4. **Patient-Specific Laboratory Orders**:
   - Seamless 1-click creation from Dental Case and treatment sessions with duplicate prevention.
   - Tooth-specific lines supporting FDI tooth notation (11-48, multi-tooth ranges for bridges).
   - Captures preparation design, VITA shade, stump die shade, digital scans (STL/PLY), and clinical notes.

5. **Integrated Quality Management**:
   - Reuses existing Quality Management module (`Quality`) without duplication.
   - Triggers quality control checks for marginal fit, shade matching, surface finish, and sterility.
   - Automatic quality alert creation on failure, quarantine handling, and linked rework/re-inspection workflow.
   - Only authorized Quality Inspectors and Lab Managers can validate checks.

6. **External Commercial Laboratory Workflow**:
   - Full tracking for work routed to outside commercial laboratories.
   - Courier airway bills, expected vs actual return dates, and incoming clinic QC verification.

7. **Finished Goods, Dispatch & Clinic Acceptance**:
   - Dispatches with internal runners or couriers.
   - Clinic receipt intake with condition and hygiene verification.
   - Mandatory dentist clinical seating acceptance (fit, occlusion, shade match) before order closure.

8. **Real-Time KPI Dashboard & Official Reports**:
   - Real-time operational dashboard with direct drill-down links.
   - Official QWeb PDF reports: Laboratory Work Order Prescription and Finished Goods Delivery Slip.
    """,
    'author': 'Dental Clinic Systems',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'product',
        'stock',
        'purchase',
        'mrp',
        'Quality',
        'account',
        'dental_base',
        'dental_patient',
        'dental_catalog',
        'dental_core',
    ],
    'data': [
        'security/dental_lab_security.xml',
        'security/ir.access.csv',
        'data/dental_lab_sequence.xml',
        'data/dental_lab_data.xml',
        'data/dental_lab_demo_data.xml',
        'wizard/create_lab_order_wizard_views.xml',
        'wizard/lab_rework_wizard_views.xml',
        'views/product_template_views.xml',
        'views/quality_check_views_inherit.xml',
        'views/quality_alert_views_inherit.xml',
        'views/mrp_production_views_inherit.xml',
        'views/dental_case_views_inherit.xml',
        'views/dental_lab_order_views.xml',
        'views/dental_lab_order_line_views.xml',
        'views/dental_lab_dispatch_views.xml',
        'views/dental_lab_receipt_views.xml',
        'views/dental_lab_dashboard_views.xml',
        'views/dental_lab_menus.xml',
        'report/lab_order_prescription_template.xml',
        'report/lab_delivery_slip_template.xml',
        'report/dental_lab_reports.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
