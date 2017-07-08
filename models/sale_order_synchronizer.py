# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,tools, _
from odoo.exceptions import UserError
from connection_parameter_setting import connection_parameter_setting
from customer_setting import customer_setting
from sale_order_setting import sale_order_setting
from idempierewsc.idempierewsc.request import QueryDataRequest
from idempierewsc.idempierewsc.request import CreateDataRequest
from idempierewsc.idempierewsc.request import SetDocActionRequest
from idempierewsc.idempierewsc.request import CompositeOperationRequest
from idempierewsc.idempierewsc.base import LoginRequest
from idempierewsc.idempierewsc.enums import WebServiceResponseStatus
from idempierewsc.idempierewsc.net import WebServiceConnection
from idempierewsc.idempierewsc.base import Field
from idempierewsc.idempierewsc.base import Operation
from idempierewsc.idempierewsc.enums import DocAction
import traceback

class sale_order_synchronizer():


    def synchronize_to_idempiere(self, order):
        print "synchronize_to_idempiere"
        connection_parameter = order.env['idempiere_synchronizer_so.connection_parameter_setting'].search([('idempiere_login_client_id', '>', '0')], limit=1)
        customer_set = order.env['idempiere_synchronizer_so.customer_setting'].search([('idempiere_web_service_type', '!=', '')], limit=1)
        saleorder_set = order.env['idempiere_synchronizer_so.sale_order_setting'].search([('idempiere_c_doctypetarget_id', '>', '0')], limit=1)
        clienteid = self.consultarCliente(connection_parameter,customer_set,order)
        if clienteid == 0:
           clienteid =  self.crearCliente(connection_parameter,order)
        if (clienteid>0):
            self.crear_order(connection_parameter,saleorder_set,clienteid,order)

    def consultarCliente(self,connection_parameter,customer_set,order):

        print('Consultando Cliente..')
        url = connection_parameter.idempiere_url
        urls = connection_parameter.idempiere_urls

        login = LoginRequest()
        login.client_id = connection_parameter.idempiere_login_client_id
        login.role_id = connection_parameter.idempiere_login_role_id
        login.password = connection_parameter.idempiere_login_password
        login.user = connection_parameter.idempiere_login_user
        login.stage =10

        ws = QueryDataRequest()
        ws.web_service_type = customer_set.idempiere_web_service_type
        ws.offset = 0
        ws.limit = 1
        ws.login = login
        odookey = str(order.partner_id[customer_set.odoo_key_column_name])
        ws.filter= customer_set.idempiere_key_column_name+" = '" +odookey+"'"

        wsc = WebServiceConnection()
        wsc.url = urls
        wsc.attempts = 3
        wsc.app_name = 'Test from python'
        clienteid = 0
        try:
            response = wsc.send_request(ws)
            wsc.print_xml_request()
            wsc.print_xml_response()

            if response.status == WebServiceResponseStatus.Error:
                print('Error: ' + response.error_message)
            else:
                print('Total Rows: ' + str(response.total_rows))
                print('Num rows: ' + str(response.num_rows))
                print('Start row: ' + str(response.start_row))
                print('')
                for row in response.data_set:
                    for field in row:
                        print(str(field.column) + ': ' + str(field.value))
                        #cr, uid = self.cr, self.uid
                        if str(field.column)=='C_BPartner_ID':
                            clienteid = int(field.value)
                        #self.description = self.description + str(field.column) + ': ' + str(field.value)
                    print('')
                print('---------------------------------------------')
                print('Web Service Type: ' + ws.web_service_type)
                print('Attempts: ' + str(wsc.attempts_request))
                print('Time: ' + str(wsc.time_request))
                self.description = 'Web Service Type: ' + ws.web_service_type
                self.description = self.description + ' \n Num rows: ' + str(response.num_rows)

        except:
            traceback.print_exc()

        return clienteid

    def crearCliente(self,connection_parameter,order):
        print('Creando Cliente..')
        clienteid=0
        url = connection_parameter.idempiere_url
        urls = connection_parameter.idempiere_urls

        login = LoginRequest()
        login.client_id = connection_parameter.idempiere_login_client_id
        login.role_id = connection_parameter.idempiere_login_role_id
        login.password = connection_parameter.idempiere_login_password
        login.user = connection_parameter.idempiere_login_user
        login.stage =10

        ws1 = CreateDataRequest()
        ws1.web_service_type = 'CreateBPartnerTest'
        ws1.data_row = [Field('Name',  str(order.partner_id.name)),
                        Field('Value', str(order.partner_id.ref)),
                        Field('TaxID', str(order.partner_id.ref))]


        ws2 = CreateDataRequest()
        ws2.web_service_type = 'CreateBPartnerContactTest'
        ws2.data_row = [Field('Name',  str(order.partner_id.name)),
                        Field('C_BPartner_ID', '@C_BPartner.C_BPartner_ID')]

        ws3 = CreateDataRequest()
        ws3.web_service_type = 'CreateBPartnerCLocation'
        ws3.data_row = [Field('C_Country_ID', '171'),
                        Field('City', str(order.partner_id.city)),
                        Field('Address1', str(order.partner_id.street))]

        ws4 = CreateDataRequest()
        ws4.web_service_type = 'CreateBPartnerBPLocation'
        ws4.data_row = [Field('Name',  str(order.partner_id.city)),
                        Field('C_Location_ID', '@C_Location.C_Location_ID'),
                        Field('C_BPartner_ID', '@C_BPartner.C_BPartner_ID')]

        ws0 = CompositeOperationRequest()
        ws0.login = login
        ws0.operations.append(Operation(ws1))
        ws0.operations.append(Operation(ws2))
        ws0.operations.append(Operation(ws3))
        ws0.operations.append(Operation(ws4))
        ws0.web_service_type = 'CompositeBPartnerTest'

        wsc = WebServiceConnection()
        wsc.url = urls
        wsc.attempts = 3
        wsc.app_name = 'Test from python'

        try:
            response = wsc.send_request(ws0)
            wsc.print_xml_request()
            wsc.print_xml_response()

            if response.status == WebServiceResponseStatus.Error:
                print('Error: ' + response.error_message)
            else:
                print('RecordID: ' + str(response.responses[0].record_id))
                clienteid = int(response.responses[0].record_id)

        except:
            traceback.print_exc()
        return clienteid

    def crear_order(self,connection_parameter,saleorder_set,clienteid,order):
        print('Creando Orden..')
        url = connection_parameter.idempiere_url
        urls = connection_parameter.idempiere_urls

        login = LoginRequest()
        login.client_id = connection_parameter.idempiere_login_client_id

        login.role_id = connection_parameter.idempiere_login_role_id
        login.password = connection_parameter.idempiere_login_password
        login.user = connection_parameter.idempiere_login_user

        ws1 = CreateDataRequest()
        ws1.web_service_type = saleorder_set.idempiere_order_web_service_type
        ws1.data_row = [Field('C_DocTypeTarget_ID', saleorder_set.idempiere_c_doctypetarget_id),
                        Field('AD_Org_ID', saleorder_set.idempiere_ad_org_id),
                        Field('C_BPartner_ID', clienteid),
                        Field('DateOrdered', order.confirmation_date),
                        Field('M_Warehouse_ID', saleorder_set.idempiere_m_warehouse_id),
                        Field('SalesRep_ID', 100),
                        Field('M_PriceList_ID', saleorder_set.idempiere_m_pricelist_id)]

        ws2lines = set()
        for line in order.order_line:
            wsline = CreateDataRequest()
            wsline.web_service_type = saleorder_set.idempiere_orderline_web_service_type

            productid = self.consultarProducto(connection_parameter,line.product_id.default_code)
            if productid >0:
                wsline.data_row =([Field('AD_Org_ID', saleorder_set.idempiere_ad_org_id),
                                Field('C_Order_ID', '@C_Order.C_Order_ID'),
                                Field('M_Product_ID', productid),
                                Field('QtyEntered', line.product_uom_qty),
                                Field('QtyOrdered', line.product_uom_qty),
                                Field('PriceList', line.price_unit),
                                Field('PriceEntered', line.price_unit),
                                Field('PriceActual', line.price_unit),
                                Field('Line', line.id)])
                ws2lines.add(wsline)

        ws3 = SetDocActionRequest()
        ws3.web_service_type = saleorder_set.idempiere_docaction_web_service_type
        ws3.doc_action = DocAction.Complete
        ws3.record_id_variable = '@C_Order.C_Order_ID'
        ws3.record_id = 0

        ws0 = CompositeOperationRequest()
        ws0.login = login
        ws0.operations.append(Operation(ws1))

        for wline in ws2lines:
            ws0.operations.append(Operation(wline))

        ws0.operations.append(Operation(ws3))
        ws0.web_service_type = saleorder_set.idempiere_composite_web_service_type

        wsc = WebServiceConnection()
        wsc.url = urls
        wsc.attempts = 3
        wsc.app_name = 'Test from python'

        try:

            response = wsc.send_request(ws0)
            wsc.print_xml_request()
            wsc.print_xml_response()

            if response.status == WebServiceResponseStatus.Error:
                print('Error: ' + response.error_message)
            else:
                print('Response: ' + str(response.web_service_response_model()))
                for res in response.responses:
                    print('Response: ' + str(res.web_service_response_model()))
                print('---------------------------------------------')
                print('Web Service Type: ' + ws0.web_service_type)
                print('Attempts: ' + str(wsc.attempts_request))
                print('Time: ' + str(wsc.time_request))
        except:
            traceback.print_exc()

    def consultarProducto(self,connection_parameter,productvalue):

        print('Consultando Producto..')
        url = connection_parameter.idempiere_url
        urls = connection_parameter.idempiere_urls

        login = LoginRequest()
        login.client_id = connection_parameter.idempiere_login_client_id
        login.role_id = connection_parameter.idempiere_login_role_id
        login.password = connection_parameter.idempiere_login_password
        login.user = connection_parameter.idempiere_login_user
        login.stage =10

        ws = QueryDataRequest()
        ws.web_service_type = 'QueryProductTest'
        ws.offset = 0
        ws.limit = 1
        ws.login = login
        odookey = str(productvalue)
        ws.filter= " Value= '" +odookey+"'"

        wsc = WebServiceConnection()
        wsc.url = urls
        wsc.attempts = 3
        wsc.app_name = 'Test from python'
        productid = 0
        try:
            response = wsc.send_request(ws)
            wsc.print_xml_request()
            wsc.print_xml_response()

            if response.status == WebServiceResponseStatus.Error:
                print('Error: ' + response.error_message)
            else:
                print('Total Rows: ' + str(response.total_rows))
                print('Num rows: ' + str(response.num_rows))
                print('Start row: ' + str(response.start_row))
                print('')
                for row in response.data_set:
                    for field in row:
                        print(str(field.column) + ': ' + str(field.value))
                        #cr, uid = self.cr, self.uid
                        if str(field.column)=='M_Product_ID':
                            productid = int(field.value)
                        #self.description = self.description + str(field.column) + ': ' + str(field.value)
                    print('')
                print('---------------------------------------------')
                print('Web Service Type: ' + ws.web_service_type)
                print('Attempts: ' + str(wsc.attempts_request))
                print('Time: ' + str(wsc.time_request))
                self.description = 'Web Service Type: ' + ws.web_service_type
                self.description = self.description + ' \n Num rows: ' + str(response.num_rows)

        except:
            traceback.print_exc()

        return productid
