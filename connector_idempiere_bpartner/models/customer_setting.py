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
    read_bpartner_wst = fields.Char('WST Read a Customer',required=True,help='Only Read a register, not create or update data')
    create_bpartner_wst = fields.Char('WST Create Business Partner',required=True,help='Web Service Type for Create a Customer or Supplier')
    create_contact_wst = fields.Char('WST Create Contact',required=True,help='Web Service Type for Create a Contact of Business Partner')
    create_bplocation_wst = fields.Char('WST Create BP Location',required=True,help='Web Service Type for associate a Location (Address) to Business Partner')
    create_location_wst = fields.Char('WST Create a Location',required=True,help='Web Service Type for Create a Location (Address)')
    composite_wst = fields.Char('WST Composite',required=True,help='Web Service Type for Group Operations')

    def getCustomerID(self,connection,partner):
        """ Obtain the idempiere record identifier (C_BPartner_ID) of a customer associated with an odoo sales order
            :param connection_parameter_setting connection
            :param res.partner partner
            :return: iDempiere's C_BPartner_ID of Customer
        """
        ws = QueryDataRequest()
        ws.web_service_type = self.read_bpartner_wst
        ws.offset = 0
        ws.limit = 1
        ws.login = connection.getLogin()
        odookey = str(partner[self.odoo_key_column_name])
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

        return customerID

    #Send the customer to be registered in idempiere
    def sendCustomer(self,connection,partner):
        """ Send the customer to be registered in idempiere
            :param connection_parameter_setting connection
            :param res.partner partner
        """
        ws1 = CreateDataRequest()
        ws1.web_service_type = self.create_bpartner_wst #WebService to create the customer
        ws1.data_row = [Field('Name',  str(partner.name)),
                        Field('Value', str(partner.ref)),
                        Field('TaxID', str(partner.ref))]


        ws2 = CreateDataRequest()
        ws2.web_service_type = self.create_contact_wst #WebService to create a contact of customer
        ws2.data_row = [Field('Name',  str(partner.name)),
                        Field('C_BPartner_ID', '@C_BPartner.C_BPartner_ID')]

        ws3 = CreateDataRequest()
        ws3.web_service_type = self.create_location_wst #WebService to create a C_Location of customer
        ws3.data_row = [Field('C_Country_ID', '171'),
                        Field('City', str(partner.city)),
                        Field('Address1', str(partner.street))]

        ws4 = CreateDataRequest()
        ws4.web_service_type = self.create_bplocation_wst #WebService to create a C_BPartner_Location of customer
        ws4.data_row = [Field('Name',  str(partner.city)),
                        Field('C_Location_ID', '@C_Location.C_Location_ID'),
                        Field('C_BPartner_ID', '@C_BPartner.C_BPartner_ID')]

        ws0 = CompositeOperationRequest()
        ws0.login = connection.getLogin()
        ws0.operations.append(Operation(ws1))
        ws0.operations.append(Operation(ws2))
        ws0.operations.append(Operation(ws3))
        ws0.operations.append(Operation(ws4))
        ws0.web_service_type = self.composite_wst #WebService composite to group the operations necessary to create a customer with its basic data

        wsc = connection.getWebServiceConnection()
        customerID = 0
        try:
            response = wsc.send_request(ws0)
            wsc.print_xml_request()
            wsc.print_xml_response()

            if response.status != WebServiceResponseStatus.Error:
                customerID = int(response.responses[0].record_id)

        except:
            traceback.print_exc()
        return customerID
