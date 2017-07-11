# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,tools, _
from odoo.exceptions import UserError
from sale_order_synchronizer import sale_order_synchronizer
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

#Class inherited from Sales Order to implement the sending of Sales Orders to iDempiere after being confirmed in Odoo
class sale_order_custom(models.Model):
    _inherit = "sale.order"

    scheduled = fields.Boolean('Scheduled for later sync',default=False)
    sync_message = fields.Char('Sync message',default='')


    #After confirming a sales order, the synchronization method is triggered.
    @api.multi
    def action_confirm(self):
        self.ensure_one()
        res = super(sale_order_custom, self).action_confirm()
        print ('Synchronizing....')
        synchronizer = sale_order_synchronizer()
        success = synchronizer.synchronize_to_idempiere(self)

        if success==False:
            message_body = "\n\n".join(self.sync_message)
            self.message_post(body=message_body, subject="Error")

        return res

    #Method to schedule a scheduled synchronization in case you can not synchronize online
    def toSchedule(self,message):
        if len(str(self.sync_message)) > 0:
            self.sync_message = str(self.sync_message) + " " +str(message)
        else:
            self.sync_message = str(message)
        self.scheduled = True

        return {
                "warning":{
                "title": _("Alert"),
                "message": self.sync_message,
                },
        }

    #Sent from the header and lines of a Sales Order to iDempiere and execution of the action of the complete document.
    def sendOrder(self,connection_parameter,clienteid,order,product_setting,sales_order_setting):

        ws1 = CreateDataRequest()
        ws1.web_service_type = sales_order_setting.idempiere_order_web_service_type
        ws1.data_row = [Field('C_DocTypeTarget_ID', sales_order_setting.idempiere_c_doctypetarget_id),
                        Field('AD_Org_ID', sales_order_setting.idempiere_ad_org_id),
                        Field('C_BPartner_ID', clienteid),
                        Field('DateOrdered', order.confirmation_date),
                        Field('M_Warehouse_ID', sales_order_setting.idempiere_m_warehouse_id),
                        Field('SalesRep_ID', 100),
                        Field('M_PriceList_ID', sales_order_setting.idempiere_m_pricelist_id),
                        Field('Description', order.name)]

        ws2lines = set()

        productNotFound = False

        for line in order.order_line:
            wsline = CreateDataRequest()
            wsline.web_service_type = sales_order_setting.idempiere_orderline_web_service_type

            productID = product_setting.getProductID(connection_parameter,line.product_id.default_code)
            if productID >0:
                wsline.data_row =([Field('AD_Org_ID', sales_order_setting.idempiere_ad_org_id),
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
        ws3.web_service_type = sales_order_setting.idempiere_docaction_web_service_type
        ws3.doc_action = DocAction.Complete
        ws3.record_id_variable = '@C_Order.C_Order_ID'
        ws3.record_id = 0

        ws0 = CompositeOperationRequest()
        ws0.login = connection_parameter.getLogin()
        ws0.operations.append(Operation(ws1))

        for wline in ws2lines:
            ws0.operations.append(Operation(wline))

        ws0.operations.append(Operation(ws3))
        ws0.web_service_type = sales_order_setting.idempiere_composite_web_service_type

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