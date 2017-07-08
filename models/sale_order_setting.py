# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from idempierewsc.request import QueryDataRequest
from idempierewsc.net import WebServiceConnection
from idempierewsc.enums import WebServiceResponseStatus
from idempierewsc.base import Operation
from idempierewsc.request import CreateDataRequest
from idempierewsc.base import Field
from idempierewsc.request import CompositeOperationRequest
from idempierewsc.enums import DocAction
from idempierewsc.request import SetDocActionRequest
import traceback

class sale_order_setting(models.Model):
    _name = 'idempiere_synchronizer_so.sale_order_setting'

    idempiere_c_doctypetarget_id = fields.Char('iDempiere C_DocTypeTarget_ID',required=True)
    idempiere_ad_org_id = fields.Char('iDempiere AD_Org_ID',required=True)
    idempiere_m_warehouse_id = fields.Char('iDempiere M_Warehouse_ID',required=True)
    idempiere_m_pricelist_id = fields.Char('iDempiere M_PriceList_ID',required=True)
    idempiere_customer_web_service_type = fields.Char('iDempiere Customer WebService Type',required=True)
    idempiere_order_web_service_type = fields.Char('iDempiere Order WebService Type',required=True)
    idempiere_orderline_web_service_type = fields.Char('iDempiere OrderLine WebService Type',required=True)
    idempiere_docaction_web_service_type = fields.Char('iDempiere DocAction WebService Type',required=True)
    idempiere_composite_web_service_type = fields.Char('iDempiere Composite WebService Type',required=True)

    def sendOrder(self,connection_parameter,clienteid,order,product_setting):

        ws1 = CreateDataRequest()
        ws1.web_service_type = self.idempiere_order_web_service_type
        ws1.data_row = [Field('C_DocTypeTarget_ID', self.idempiere_c_doctypetarget_id),
                        Field('AD_Org_ID', self.idempiere_ad_org_id),
                        Field('C_BPartner_ID', clienteid),
                        Field('DateOrdered', order.confirmation_date),
                        Field('M_Warehouse_ID', self.idempiere_m_warehouse_id),
                        Field('SalesRep_ID', 100),
                        Field('M_PriceList_ID', self.idempiere_m_pricelist_id),
                        Field('Description', order.name)]

        ws2lines = set()

        productNotFound = False

        for line in order.order_line:
            wsline = CreateDataRequest()
            wsline.web_service_type = self.idempiere_orderline_web_service_type

            productID = product_setting.getProductID(connection_parameter,line.product_id.default_code)
            if productID >0:
                wsline.data_row =([Field('AD_Org_ID', self.idempiere_ad_org_id),
                                Field('C_Order_ID', '@C_Order.C_Order_ID'),
                                Field('M_Product_ID', productID),
                                Field('QtyEntered', line.product_uom_qty),
                                Field('QtyOrdered', line.product_uom_qty),
                                Field('PriceList', line.price_unit),
                                Field('PriceEntered', line.price_unit),
                                Field('PriceActual', line.price_unit),
                                Field('Line', line.id)])
                ws2lines.add(wsline)
            else:
                productNotFound = True
                order.toSchedule(_("Product Not Found")+ " " + line.product_id.default_code)

        if productNotFound:
            return False

        ws3 = SetDocActionRequest()
        ws3.web_service_type = self.idempiere_docaction_web_service_type
        ws3.doc_action = DocAction.Complete
        ws3.record_id_variable = '@C_Order.C_Order_ID'
        ws3.record_id = 0

        ws0 = CompositeOperationRequest()
        ws0.login = connection_parameter.getLogin()
        ws0.operations.append(Operation(ws1))

        for wline in ws2lines:
            ws0.operations.append(Operation(wline))

        ws0.operations.append(Operation(ws3))
        ws0.web_service_type = self.idempiere_composite_web_service_type

        wsc = connection_parameter.getWebServiceConnection()

        try:

            response = wsc.send_request(ws0)
            wsc.print_xml_request()
            wsc.print_xml_response()

            if response.status == WebServiceResponseStatus.Error:
                order.toSchedule(_(response.error_message))
                return False
            else:
                return True
        except:
            traceback.print_exc()
            order.toSchedule(_("Sync Error"))
            return False