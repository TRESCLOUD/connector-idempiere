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
from datetime import datetime, date, time, timedelta
import traceback


#Class inherited from Sales Order to implement the sending of Sales Orders to iDempiere after being confirmed in Odoo
class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_delivery_policy(self):
        """
        This function load the default delivery policy using the partners default
        """
        return self.partner_id.delivery_policy if self.partner_id else 'M'

    
    delivery_policy_selection = [
        ('A', 'Availability'),
        ('F', 'Force'),
        ('L', 'Complete Line'),
        ('M', 'Manual'),
        ('O', 'Complete Order'),
        ('R', 'After Receipt')]

    #columns
    idempiere_document_type_id = fields.Many2one('idempiere.document.type', 
                                                 string='Document', 
                                                 required=True, 
                                                 readonly=True, 
                                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                                 help="iDempiere document, automatically sets the organization, warehouse, and other internal parameters", 
                                                 track_visibility='onchange',)
    
    idempiere_sale_description = fields.Text(    'Sale Description', 
                                                 readonly=True, 
                                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                                 help="Short description of this sale", 
                                                 track_visibility='onchange',)

    delivery_policy = fields.Selection(          delivery_policy_selection, 
                                                 readonly=True, 
                                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                                 help='Allow the user select the delivery policy type to be use in sale order',
                                                 track_visibility='onchange', 
                                                 default=_default_delivery_policy,)
    partner_invoice_id = fields.Many2one(        required=False)
    
    partner_shipping_id = fields.Many2one(       required=False)
    
    contact_invoice_id = fields.Many2one(        'res.partner', 
                                                 string='Contact Invoice Address', 
                                                 readonly=True, 
                                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                                 help="Contact Invoice address for current sales order.",
                                                 track_visibility='onchange',)
    
    contact_shipping_id = fields.Many2one(       'res.partner', string='Contact Delivery Address', 
                                                 readonly=True,
                                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                                 help="Contact Delivery address for current sales order.",
                                                 track_visibility='onchange',)

    c_order_id = fields.Integer(                 "ID from iDempiere",
                                                 readonly=True,
                                                 copy=False,
                                                 help='Show the related ID from iDempiere',
                                                 track_visibility='onchange',)
    #TODO: Implementar estos campos
    scheduled = fields.Boolean('Scheduled for later sync',default=False)
    sync_message = fields.Char('Sync message',default='')
    
    @api.multi
    def open_page(self):
        connector_idempiere = self.env['connector_idempiere.connection_parameter_setting'].search([],limit=1)
        if not self.c_order_id:
            return {
                    "type": "ir.actions.act_url",
                    "url": "#",
                    }
        url = connector_idempiere.idempiere_url + '/webui/?Action=Zoom&TableName=C_Order&Record_ID=' + str(self.c_order_id)
        return {
                "type": "ir.actions.act_url",
                "url": url,
                "target": "new",
                }


    @api.multi
    def get_fields_required_idempiere(self):
        """ list 'not required' field of required fields to validate before sending to idempiere
        """
        __FIELDS_REQUIRED_IDEMPIERE = ['idempiere_document_type_id', 'delivery_policy',
                         'contact_invoice_id', 'contact_shipping_id',
                         'partner_invoice_id','partner_shipping_id']
        return __FIELDS_REQUIRED_IDEMPIERE 
    
    @api.multi
    def action_confirm(self):
        """ After confirming a sales order, the synchronization method is triggered.
        """
        self.ensure_one()
        res = super(SaleOrder, self).action_confirm()

        error_fields = []
        for field in self.get_fields_required_idempiere():
            if not self[field]:
                error_fields.append(self.fields_get([field], ['string'])[field]['string'])
                
        if error_fields:
            raise UserError(_(u'Error: \n\nLos siguientes campos no están llenados, '
                              u'por favor elegir los datos de esos campos para '
                              u'continuar con la venta: \n- %s') % '\n- '.join(error_fields))
        print ('Synchronizing....')
        synchronizer = sale_order_synchronizer()
        idempiere_sale_id = synchronizer.synchronize_to_idempiere(self)
        if idempiere_sale_id==False:
            raise UserError(_('Error iDempiere: %s') % self.sync_message)
            message_body = "\n\n".join(self.sync_message)
            self.message_post(body=message_body, subject="Error")        
        #si success retorno el id de la orden de venta en idempiere:
        for order in self:
            order.c_order_id = idempiere_sale_id
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

    def sendOrder(self,connection_parameter,order,product_setting,sales_order_setting,customer_setting):
        """Sent from the header and lines of a Sales Order to iDempiere and execution of the action of the complete document.
        """
        ws1 = CreateDataRequest()
        ws1.web_service_type = sales_order_setting.idempiere_order_web_service_type

        dateOrdered = fields.Datetime.from_string(self.confirmation_date)
        dateOrdered_user = fields.Datetime.to_string((fields.Datetime.context_timestamp(self,dateOrdered)))
        datePromised = fields.Datetime.from_string(self.commitment_date)
        datePromised_user = fields.Datetime.to_string((fields.Datetime.context_timestamp(self,datePromised)))

        C_BPartner_ID = customer_setting.getCustomerID(connection_parameter,order.partner_id)
        if C_BPartner_ID == 0:
           C_BPartner_ID =  customer_setting.createBPartner(connection_parameter,order.partner_id)
           self.partner_id.C_Idempiere_ID = C_BPartner_ID 
        invoiceContact = customer_setting.getContactID(connection_parameter,self.contact_invoice_id,C_BPartner_ID)
        if invoiceContact==0:
            invoiceContact = customer_setting.createContact(connection_parameter,self.contact_invoice_id,C_BPartner_ID)
            self.contact_invoice_id.C_Idempiere_ID = invoiceContact 
        deliveryContact = customer_setting.getContactID(connection_parameter,self.contact_shipping_id,C_BPartner_ID)
        if deliveryContact==0:
            deliveryContact=customer_setting.createContact(connection_parameter,self.contact_shipping_id,C_BPartner_ID)
            self.contact_shipping_id.C_Idempiere_ID = deliveryContact
        invoiceAddress = customer_setting.getInvoiceAddressID(connection_parameter,order.partner_invoice_id,C_BPartner_ID)
        if invoiceAddress == 0:
            invoiceAddress = customer_setting.createInvoiceAddress(connection_parameter,order.partner_invoice_id,C_BPartner_ID)
            self.partner_invoice_id.C_Idempiere_ID = invoiceAddress 
        deliveryAddress = customer_setting.getDeliveryAddressID(connection_parameter,order.partner_shipping_id,C_BPartner_ID)
        if deliveryAddress == 0:
            deliveryAddress = customer_setting.createDeliveryAddress(connection_parameter,order.partner_shipping_id,C_BPartner_ID)
            self.partner_shipping_id.C_Idempiere_ID = deliveryAddress
        customer_reference = self.name
        if self.client_order_ref:
            customer_reference += "-"+self.client_order_ref 
        ws1.data_row = [Field('C_DocTypeTarget_ID', self.idempiere_document_type_id.c_doctype_id),
                        Field('C_Currency_ID', 100), #TODO Incorporar multimoneda
                        Field('AD_Org_ID', self.idempiere_document_type_id.ad_org_id),
                        Field('C_BPartner_ID', C_BPartner_ID),
                        Field('DateOrdered', dateOrdered_user),
                        Field('M_Warehouse_ID', self.idempiere_document_type_id.m_warehouse_id),
                        Field('SalesRep_ID', 100),
                        Field('M_PriceList_ID', sales_order_setting.idempiere_m_pricelist_id),
                        Field('Description', self.idempiere_sale_description),
                        Field('DeliveryRule', self.delivery_policy),
                        Field('DatePromised',datePromised_user),
                        Field('C_PaymentTerm_ID',order.payment_term_id.C_PaymentTerm_ID),
                        Field('POReference',customer_reference),
                        Field('AD_User_ID',deliveryContact),
                        Field('Bill_User_ID',invoiceContact),
                        Field('C_BPartner_Location_ID',deliveryAddress),
                        Field('Bill_Location_ID',invoiceAddress),
                        Field('Bill_BPartner_ID',C_BPartner_ID)]
        idempiere_extra_header_fields = self.idempiere_extra_header_fields()
        if idempiere_extra_header_fields:
            ws1.data_row.extend(idempiere_extra_header_fields) 

        ws2lines = set()

        productNotFound = False

        for line in order.order_line:
            wsline = CreateDataRequest()
            wsline.web_service_type = sales_order_setting.idempiere_orderline_web_service_type

            productID = product_setting.getProductID(connection_parameter,line.product_id.default_code)
            if productID >0:
                daysPromised = 0
                if line.customer_lead:
                    daysPromised = int(line.customer_lead)
                daysPromised = timedelta(days=daysPromised)
                datePromisedLine = fields.Datetime.context_timestamp(self,dateOrdered) + daysPromised
                wsline.data_row =([Field('AD_Org_ID', self.idempiere_document_type_id.ad_org_id),
                                Field('C_Order_ID', '@C_Order.C_Order_ID'),
                                Field('M_Product_ID', productID),
                                Field('QtyEntered', line.product_uom_qty),
                                Field('QtyOrdered', line.product_uom_qty),
                                Field('C_UOM_ID',line.product_uom.c_uom_id),
                                Field('PriceEntered', line.price_unit), #podria usarse el price_reduce, pero para el caso de uso esta bien price_unit
                                Field('PriceList', line.price_unit),
                                Field('PriceActual', line.price_unit),
                                #Field('Discount', 0.0), #0% para el caso de uso
                                #Field('LineNetAmt',line.price_subtotal),
                                Field('Line', line.sequence),
                                Field('Description', line.name),
                                Field('DatePromised',datePromisedLine)
                                ])
                idempiere_extra_line_fields = order.order_line.idempiere_extra_line_fields()
                if idempiere_extra_line_fields:
                    wsline.data_row.extend(idempiere_extra_line_fields)
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

        response = wsc.send_request(ws0)
        wsc.print_xml_request()
        wsc.print_xml_response()

        if response.status == WebServiceResponseStatus.Error:
            order.toSchedule(_(response.error_message))
            return False
        
        #intentamos obtener el documento origen
        C_Order_ID = response.responses[0].record_id
        #TODO Almacenar el id de idempiere de la venta creada
        return C_Order_ID

        #en este sprint no hacemos offline
        #except:
        #    traceback.print_exc()
        #    order.toSchedule(_("Sync Error"))
        #    return False
        
    @api.multi
    def idempiere_extra_header_fields(self):
        """
        Permite agregar campos adicionales a la cabecera de venta a enviar a idempiere
        Para ser usado por modulos que hereden de este 
        """
        header = []
        return header
            
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - contact_invoice_id
        - contact_shipping_id
        - delivery_policy
        """

        res = super(SaleOrder, self).onchange_partner_id()
        if not self.partner_id:
            self.update({
                'contact_invoice_id': False,
                'contact_shipping_id': False,
                'delivery_policy': False,
            })
            return

        addr = self.partner_id.address_get_idempiere(['delivery', 'invoice','contact'])
        values = {
            'contact_invoice_id': addr['contact'],
            'contact_shipping_id': addr['contact'],
            'partner_invoice_id': addr['invoice'] or addr['delivery'], #usamos cualquier direccion
            'partner_shipping_id': addr['delivery'] or addr['invoice'], #usamos cualquier direccion
            'delivery_policy': self.partner_id.delivery_policy if self.partner_id else False,
            }
        self.update(values)
        return res



class SaleOrderLine(models.Model):
    '''
    Heredando de la clase sale_order line
    '''
    _inherit = 'sale.order.line'

    @api.multi
    def idempiere_extra_line_fields(self):
        """
        Permite agregar campos adicionales a la linea de venta a enviar a idempiere
        Para ser usado por modulos que hereden de este 
        """
        line = []
        return line
