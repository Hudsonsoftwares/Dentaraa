# -*- coding: utf-8 -*-
{
    'name': 'Dental Pharmacy Management',
    'version': '20.0.1.0.0',
    'category': 'Healthcare/Dental',
    'summary': 'Comprehensive Dental Pharmacy, Medicine Catalog, Prescriptions, Batch Dispensing, Inventory & Billing Integration',
    'description': """
Dental Pharmacy Management Module for Odoo 20 Community Edition
===============================================================
A complete clinical and retail pharmacy management system designed specifically for Dental Clinics.

Key Capabilities:
-----------------
1. **Medicine Catalog**:
   - Manages generic names, dental categories, dosage forms, strengths, manufacturers, dosage units.
   - Batch tracking with barcodes and reorder thresholds.
   - Strict role-based protection of commercial purchase costs and supplier margins.

2. **Interactive Pharmacy Dashboard**:
   - Live OWL dashboard with real database counts for medicines, inventory levels, near-expiry and expired batches, and prescription queues.
   - 1-click drill-downs into filtered records.

3. **Prescription Lifecycle Management**:
   - Integrates with dental patients, cases, appointments, and prescribing dentists.
   - Captures dose, route, frequency, duration, quantity, clinical instructions, and allergy alerts.
   - States: Draft, Confirmed, Partially Dispensed, Fully Dispensed, and Cancelled with audit trails.

4. **Traceable Dispensing Workflow**:
   - Pharmacist batch/lot selection with real-time stock availability and FEFO expiry verification.
   - Strict prevention of negative inventory, over-dispensing, expired batches, and concurrent race conditions.
   - Automated creation of valid Odoo stock pickings and move lines.
   - Authorized manager returns and corrections with full audit logging.

5. **Seamless Accounting & Billing Integration**:
   - Directly links eligible dispensed items to customer invoices in the existing custom Accounting suite (`account.move`).
   - Prevents duplicate invoice creation while maintaining strict separation between clinical dispensing and financial payment.

6. **Procurement & Auditing Reports**:
   - Direct integration with Odoo Purchase for vendor replenishment.
   - Official PDF reports for Prescriptions (Rx) and Pharmacy Dispense Receipts.
   - Analytical reporting for stock levels, batch expirations, dispensing history, and pending prescriptions.
    """,
    'author': 'Dental Clinic Systems',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'product',
        'stock',
        'purchase',
        'account',
        'dental_base',
        'dental_patient',
        'dental_catalog',
        'dental_core',
    ],
    'data': [
        'security/ir.access.csv',
        'data/dental_pharmacy_sequence.xml',
        'data/dental_medicine_category_data.xml',
        'data/dental_medicine_demo_data.xml',
        'views/dental_medicine_category_views.xml',
        'views/product_template_views.xml',
        'views/stock_lot_views.xml',
        'views/dental_prescription_views.xml',
        'views/dental_pharmacy_dispense_views.xml',
        'views/dental_case_views_inherit.xml',
        'views/res_partner_views_inherit.xml',
        'views/account_move_views_inherit.xml',
        'views/pharmacy_dashboard_views.xml',
        'views/pharmacy_report_views.xml',
        'views/dental_pharmacy_menus.xml',
        'report/pharmacy_reports.xml',
        'report/prescription_report_template.xml',
        'report/dispense_receipt_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dental_pharmacy/static/src/css/pharmacy_dashboard.scss',
            'dental_pharmacy/static/src/js/pharmacy_dashboard.js',
            'dental_pharmacy/static/src/xml/pharmacy_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
