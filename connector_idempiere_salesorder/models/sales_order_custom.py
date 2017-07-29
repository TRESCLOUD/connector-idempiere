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

    @api.model
    def _default_delivery_policy(self):
        """
        This function load the default delivery policy using the partners default
        """
        return self.partner_id.delivery_policy if self.partner_id else False

    delivery_policy_selection = [
        ('A', 'Availability'),
        ('F', 'Force'),
        ('L', 'Complete Line'),
        ('M', 'Manual'),
        ('O', 'Complete Order'),
        ('R', 'After Receipt')]

    # Columns
    scheduled = fields.Boolean('Scheduled for later sync',default=False)
    sync_message = fields.Char('Sync message',default='')
    
    # Columns TRESCLOUD
    delivery_policy = fields.Selection(delivery_policy_selection, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                       track_visibility='always', default=_default_delivery_policy,
                                       help='Allow the user select the delivery policy type to be use in sale order')
    contact_invoice_id = fields.Many2one('res.partner', string='Contact Invoice Address', 
                                         readonly=True, required=True, 
                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                         help="Contact Invoice address for current sales order.")
    contact_shipping_id = fields.Many2one('res.partner', string='Contact Delivery Address', 
                                          readonly=True, required=True,
                                          states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                          help="Contact Delivery address for current sales order.")

    @api.multi
    def action_confirm(self):
        """ After confirming a sales order, the synchronization method is triggered.
        """
        self.ensure_one()
        res = super(sale_order_custom, self).action_confirm()
        print ('Synchronizing....')
        synchronizer = sale_order_synchronizer()
        success = synchronizer.synchronize_to_idempiere(self)

        if success==False:
            raise UserError(_('Error iDempiere: %s') % self.sync_message)
            message_body = "\n\n".join(self.sync_message)
            self.message_post(body=message_body, subject="Error")

        return res

    def toSchedule(self,message):
        """ Method to schedule a scheduled synchronization in case you can not synchronize online
        """
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

    def sendOrder(self,connection_parameter,clienteid,order,product_setting,sales_order_setting):
        """Sent from the header and lines of a Sales Order to iDempiere and execution of the action of the complete document.
        """
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
                order.toSchedule(_("Product Not Found")+ " " + str(line.product_id.default_code))

        if productNotFound:
            return False

        #ws3 = SetDocActionRequest()
        #ws3.web_service_type = sales_order_setting.idempiere_docaction_web_service_type
        #ws3.doc_action = DocAction.Complete
        #ws3.record_id_variable = '@C_Order.C_Order_ID'
        #ws3.record_id = 0

        ws0 = CompositeOperationRequest()
        ws0.login = connection_parameter.getLogin()
        ws0.operations.append(Operation(ws1))

        for wline in ws2lines:
            ws0.operations.append(Operation(wline))

        #ws0.operations.append(Operation(ws3))
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
        
    # TRESCLOUD
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - contact_invoice_id
        - contact_shipping_id
        - delivery_policy
        """
        
        super(sale_order_custom, self).onchange_partner_id()
        if not self.partner_id:
            self.update({
                'contact_invoice_id': False,
                'contact_shipping_id': False,
                'delivery_policy': False,
            })
            return

        addr = self.partner_id.address_get()
        values = {
            'contact_invoice_id': addr['contact'],
            'contact_shipping_id': addr['contact'],
            'delivery_policy': self.partner_id.delivery_policy if self.partner_id else False,         
       }
        self.update(values)
