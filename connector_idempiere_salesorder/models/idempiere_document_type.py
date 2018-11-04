# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class IdempiereDocumentType(models.Model):   
    _name = 'idempiere.document.type'
    _order = 'name'
    _inherit = ['mail.thread']
    
#     @api.multi
#     def name_get(self):
#         '''
#         Concatena el código y el nombre del tipo de documento
#         '''           
#         result = []
#         for document in self:
#             new_name = (document.code and '[' + document.code + '] ' or '') + document.name
#             result.append((document.id, new_name))
#         return result
    
#     @api.model
#     def name_search(self, name, args=None, operator='ilike', limit=100):
#         '''
#         Permite buscar ya sea por nombre o por codigo del tipo de documento
#         '''
#         if args is None:
#             args = []
#         domain = []
#         if name:
#             domain = ['|', ('code', operator, name), ('name', operator, name)]
#         document = self.search(domain + args, limit=limit)
#         return document.name_get()
    
    
    #Columns
    
    name = fields.Char('Document Name', size=128, track_visibility='onchange',
                       required=True,
                       help='The document name as shown in iDempmiere')
    
    c_doctype_id = fields.Integer('iDempiere c_doctype_id',
                                  required=True, 
                                  help='The database ID of the document in iDempiere')

    organization = fields.Char('Organization', size=128, track_visibility='onchange',
                               required=True,
                               help='The organization name as shown in iDempmiere, for informative purposes only')
    
    ad_org_id = fields.Integer('iDempiere ad_org_id',
                               required=True, 
                               help='The database ID of the organization in iDempiere')

    warehouse = fields.Char('Warehouse', size=128, track_visibility='onchange',
                            required=True,
                            help='The warehouse name as shown in iDempmiere')
    
    m_warehouse_id = fields.Integer('iDempiere m_warehouse_id',
                                    required=True, 
                                    help='The database ID of the warehouse in iDempiere')

    quotation = fields.Boolean('Quotation Doctype')