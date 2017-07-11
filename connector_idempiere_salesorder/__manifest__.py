# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Connector iDempiere (Sales Order)",

    'summary': """
    Sales Order Synchronizer between odoo and idempiere
    through iDempire WebService""",

    'description': """
    Sales Order Synchronizer between Odoo and Idempiere,

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
    'depends': ['base','sale','connector_idempiere','connector_idempiere_bpartner','connector_idempiere_product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_setting.xml',
        'views/sale_order_custom.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}