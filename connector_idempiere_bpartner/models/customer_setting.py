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
import traceback

#Configuration class of basic parameters for Customer synchronization
class customer_setting(models.Model):
    _name = 'connector_idempiere_bpartner.customer_setting'

    odoo_key_column_name = fields.Char('Odoo Key Column Name',required=True)
    idempiere_key_column_name = fields.Char('iDempiere Key Column Name',required=True)
    idempiere_web_service_type = fields.Char('iDempiere WebService Type',required=True)

    #Obtain the idempiere record identifier (C_BPartner_ID) of a customer associated with an odoo sales order
    def getCustomerID(self,connection,odooOrder):

        ws = QueryDataRequest()
        ws.web_service_type = self.idempiere_web_service_type
        ws.offset = 0
        ws.limit = 1
        ws.login = connection.getLogin()
        odookey = str(odooOrder.partner_id[self.odoo_key_column_name])
        ws.filter= self.idempiere_key_column_name+" = '" +odookey+"'"
        wsc = connection.getWebServiceConnection()

        customerID = 0
        try:
            response = wsc.send_request(ws)
            wsc.print_xml_request()
            wsc.print_xml_response()
            if response.status == WebServiceResponseStatus.Error:
                traceback.print_exc()
            else:
                for row in response.data_set:
                    customerID = int(row[0].value)
        except:
            traceback.print_exc()
            odooOrder.toSchedule(_("Error on get Customer"))

        return customerID

    #Send the customer to be registered in idempiere
    def sendCustomer(self,connection,odooOrder):

        ws1 = CreateDataRequest()
        ws1.web_service_type = 'CreateBPartnerTest' #WebService to create the customer
        ws1.data_row = [Field('Name',  str(odooOrder.partner_id.name)),
                        Field('Value', str(odooOrder.partner_id.ref)),
                        Field('TaxID', str(odooOrder.partner_id.ref))]


        ws2 = CreateDataRequest()
        ws2.web_service_type = 'CreateBPartnerContactTest' #WebService to create a contact of customer
        ws2.data_row = [Field('Name',  str(odooOrder.partner_id.name)),
                        Field('C_BPartner_ID', '@C_BPartner.C_BPartner_ID')]

        ws3 = CreateDataRequest()
        ws3.web_service_type = 'CreateBPartnerCLocation' #WebService to create a C_Location of customer
        ws3.data_row = [Field('C_Country_ID', '171'),
                        Field('City', str(odooOrder.partner_id.city)),
                        Field('Address1', str(odooOrder.partner_id.street))]

        ws4 = CreateDataRequest()
        ws4.web_service_type = 'CreateBPartnerBPLocation' #WebService to create a C_BPartner_Location of customer
        ws4.data_row = [Field('Name',  str(odooOrder.partner_id.city)),
                        Field('C_Location_ID', '@C_Location.C_Location_ID'),
                        Field('C_BPartner_ID', '@C_BPartner.C_BPartner_ID')]

        ws0 = CompositeOperationRequest()
        ws0.login = connection.getLogin()
        ws0.operations.append(Operation(ws1))
        ws0.operations.append(Operation(ws2))
        ws0.operations.append(Operation(ws3))
        ws0.operations.append(Operation(ws4))
        ws0.web_service_type = 'CompositeBPartnerTest' #WebService composite to group the operations necessary to create a customer with its basic data

        wsc = connection.getWebServiceConnection()
        customerID = 0
        try:
            response = wsc.send_request(ws0)
            wsc.print_xml_request()
            wsc.print_xml_response()

            if response.status == WebServiceResponseStatus.Error:
                odooOrder.toSchedule(_(response.error_message))
            else:
                customerID = int(response.responses[0].record_id)

        except:
            traceback.print_exc()
            odooOrder.toSchedule(_("Unsent Customer"))
        return customerID
