{
    'name': 'Dental Core',
    'version': '1.0.1',
    'category': 'Healthcare/Dental',
    'summary': 'Clinical consultation and treatment management for Dental Clinics',
    'description': """
Dental Core Module
==================
Builds the clinical consultation and treatment management foundation that starts after a patient checks in for an appointment.

Key Features:
- Dental Cases
- Clinical Examinations
- Diagnoses
- Treatment Plans
- Treatment Sessions
    """,
    'depends': [
        'base',
        'dental_base',
        'dental_patient',
        'dental_catalog',
        'dental_appointment',
        'hr',
        'mail',
        'account',
    ],
    'data': [
        'security/ir.access.csv',
        'data/dental_case_sequence.xml',
        'data/dental_tooth_finding_sequence.xml',
        'data/dental_treatment_plan_sequence.xml',
        'views/dental_case_views.xml',
        'views/dental_tooth_finding_views.xml',
        'views/dental_clinical_examination_views.xml',
        'views/dental_diagnosis_views.xml',
        'views/dental_treatment_plan_views.xml',
        'views/dental_appointment_views_inherit.xml',
        'views/res_partner_views_inherit.xml',
        'views/dental_core_menus.xml',
        'views/dental_dashboards.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dental_core/static/lib/three.min.js',
            'dental_core/static/lib/OrbitControls.js',
            'dental_core/static/lib/meshopt_decoder.js',
            'dental_core/static/lib/GLTFLoader.js',
            'dental_core/static/src/css/dentist_dashboard.scss',
            'dental_core/static/src/js/admin_dashboard.js',
            'dental_core/static/src/xml/admin_dashboard.xml',
            'dental_core/static/src/js/dentist_dashboard.js',
            'dental_core/static/src/xml/dentist_dashboard.xml',
            'dental_core/static/src/js/receptionist_dashboard.js',
            'dental_core/static/src/xml/receptionist_dashboard.xml',
            'dental_core/static/src/css/dental_odontogram_3d.scss',
            'dental_core/static/src/js/dental_odontogram_3d.js',
            'dental_core/static/src/xml/dental_odontogram_3d.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
