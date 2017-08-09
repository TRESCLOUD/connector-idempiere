# -*- coding: utf-8 -*-

from operator import itemgetter

from odoo import api, fields, models,tools, _

#Class inherited from Product Uom
class ProductUom(models.Model):
    _inherit = 'product.uom'

    # Columns
    c_uom_id = fields.Integer("ID from iDempiere",
                              help='Show the related ID from iDempiere')
    
#Class inherited from Product Template
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Columns
    #idempiere_id
    m_product_id = fields.Integer("ID from iDempiere",
                                  help='Show the related ID from iDempiere')