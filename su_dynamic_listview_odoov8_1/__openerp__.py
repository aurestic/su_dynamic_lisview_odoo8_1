# -*- coding: utf-8 -*-
# © 2017 truongdung
# © 2018 Diagram Software S.L.

{
    'name': 'Dynamic ListView Advance Odoo8',
    'summary': 'Change The Odoo List view On the fly without any technical knowledge',
    'version': '8.0.1.3',
    'category': 'Web',
    'description': """
        Dynamic ListView Advance Odoo8
    """,
    'author': "truongdung <truongdung.vd@gmail.com>, "
              "Diagram Software, S.L.",
    'depends': ['web'],
    'data': [
        'security/show_fields_security.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/show_fields_view.xml',
    ],
    'price': 250,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
    'qweb': ['static/src/xml/base.xml'],
    'images': [
        'static/description/module_image.png',
    ],
}
