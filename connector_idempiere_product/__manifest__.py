# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Connector iDempiere (Product)",

    'summary': """
    Product Synchronizer between odoo and idempiere
    through iDempire WebService""",

    'description': """
    Basic connection between odoo and idempiere,

    Using Book Libraries of Saúl Piña sauljabin@gmail.com
    https://github.com/sauljabin/idempierewsc-python
    """,

    'author': "TRESCLOUD CIA LTDA - Contributor: Freddy Heredia",
    'website': "http://www.trescloud.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','connector_idempiere','sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_setting.xml',
        'views/product_custom.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}