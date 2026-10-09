{
    'name': 'Dental Clinic Management - Base',
    'version': '20.0.1.0.0',
    'category': 'Dental Clinic',
    'summary': 'Common foundation, branch management, security roles, and settings for Dental Clinic Suite',
    'description': """
Dental Clinic Management - Base Foundation
==========================================
Provides the foundational configuration, security groups, clinic & branch management,
and multi-company infrastructure for all Dental Clinic Management modules.

Key Features:
-------------
* Clinic & Branch Configuration with multi-company support
* Role-based security infrastructure:
  - Dental Administrator
  - Clinic Manager
  - Dentist
  - Dental Assistant
  - Receptionist
  - Lab Technician
  - Pharmacist
* Staff & Doctor extensions (Dental roles, registration numbers, digital signatures)
* Clinic settings (Tooth numbering standards FDI/Universal/Palmer, slot duration, etc.)
* Base menu and configuration hub for the Dental suite
* Full chatter and mail thread audit trails
    """,
    'author': 'Dental Clinic Systems',
    'depends': [
        'base',
        'mail',
        'hr',
        'contacts',
    ],
    'data': [
        'security/dental_security.xml',

        'views/res_company_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/dental_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
