# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


#Configuration class of basic parameters for Sales Order synchronization
class sale_order_setting(models.Model):
    _name = 'connector_idempiere_salesorder.sale_order_setting'

    idempiere_c_doctypetarget_id = fields.Char('iDempiere C_DocTypeTarget_ID',required=True)
    idempiere_ad_org_id = fields.Char('iDempiere AD_Org_ID',required=True)
    idempiere_m_warehouse_id = fields.Char('iDempiere M_Warehouse_ID',required=True)
    idempiere_m_pricelist_id = fields.Char('iDempiere M_PriceList_ID',required=True)
    idempiere_customer_web_service_type = fields.Char('iDempiere Customer WebService Type',required=True)
    idempiere_order_web_service_type = fields.Char('iDempiere Order WebService Type',required=True)
    idempiere_orderline_web_service_type = fields.Char('iDempiere OrderLine WebService Type',required=True)
    idempiere_docaction_web_service_type = fields.Char('iDempiere DocAction WebService Type',required=True)
    idempiere_composite_web_service_type = fields.Char('iDempiere Composite WebService Type',required=True)

