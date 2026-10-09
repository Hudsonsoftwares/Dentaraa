{
    'name': 'Dental Catalog',
    'version': '1.0',
    'category': 'Healthcare/Dental',
    'summary': 'Dental Treatments and Catalog Management',
    'description': """
        Manage Dental Treatments using Odoo's product system.
        Adds dental-specific fields to products and organizes them into treatments.
    """,
    'author': 'Your Company',
    'depends': ['dental_base', 'product', 'sale'],
    'data': [
        'security/ir.access.csv',
        'views/dental_treatment_category_views.xml',
        'views/product_template_views.xml',
        'views/dental_catalog_menus.xml',
        'data/dental_treatment_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
