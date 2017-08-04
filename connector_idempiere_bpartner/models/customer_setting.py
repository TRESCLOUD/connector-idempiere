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
    read_bpartner_wst = fields.Char('WST Read a Customer',required=True,default='',help='Only Read a register, not create or update data')
    read_contact_wst = fields.Char('WST Read a Contact',required=True,default='',help='Read a Contact of Customer From AD_User')
    read_bplocation_wst = fields.Char('WST Read a BP Location',required=True,default='',help='Read a Business Partner Location of Customer From C_BPartner_Location')
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
        odookey = str(partner[self.odoo_key_column_name])
        filter = self.idempiere_key_column_name+" = '" +odookey+"'"
        customerID = connection.getRecordID(self.read_bpartner_wst,filter,'C_BPartner_ID')

        return customerID

    def getContactID(self,connection,contact,c_bpartner_id):
        """ Obtain the idempiere record identifier (AD_User_ID) of a customer' contact associated with an odoo sales order
            :param connection_parameter_setting connection
            :param res.partner contact (Type = Contact)
            :param int c_bpartner_id
            :return: iDempiere's AD_User_ID of Contact
        """
        filter = "Name = " + contact.name + " AND C_BPartner_ID = "+c_bpartner_id
        AD_User_ID = connection.getRecordID(self.read_contact_wst,filter,'AD_User_ID')

        return AD_User_ID

    def getInvoiceAddressID(self,connection,address,c_bpartner_id):
        """ Obtain the idempiere record identifier (C_BPartner_Location) of a Invoice customer'address associated with an odoo sales order
            :param connection_parameter_setting connection
            :param res.partner address (Type = Delivery)
            :param int c_bpartner_id
            :return: iDempiere's AD_User_ID of Contact
        """
        filter = "Name = " + address.name + " AND C_BPartner_ID = "+c_bpartner_id+" AND IsBillTo = 'Y'"
        C_BPartner_Location_ID = connection.getRecordID(self.read_bplocation_wst,filter,'C_BPartner_Location_ID')

        return C_BPartner_Location_ID

    def getDeliveryAddressID(self,connection,address,c_bpartner_id):
        """ Obtain the idempiere record identifier (C_BPartner_Location) of a Delivery customer'address associated with an odoo sales order
            :param connection_parameter_setting connection
            :param res.partner address (Type = Delivery)
            :param int c_bpartner_id
            :return: iDempiere's AD_User_ID of Contact
        """
        filter = "Name = " + address.name + " AND C_BPartner_ID = "+c_bpartner_id+" AND IsShipTo = 'Y'"
        C_BPartner_Location_ID = connection.getRecordID(self.read_bplocation_wst,filter,'C_BPartner_Location_ID')

        return C_BPartner_Location_ID


    def createBPartner(self,connection,partner):
        """ Send the customer to be registered in idempiere
            :param connection_parameter_setting connection
            :param res.partner partner
            :return: int New C_BPartner_ID
        """
        #WebService to create the customer
        fields = [Field('Name',  str(partner.name)),
                  Field('Value', str(partner.vat)),
                  Field('TaxID', str(partner.vat))]

        C_BPartner_ID = connection.sendRegister(self.create_bpartner_wst,fields)

        return C_BPartner_ID

    def createContact(self,connection,contact,c_bpartner_id):
        """ Send the customer to be registered in idempiere
            :param connection_parameter_setting connection
            :param res.partner partner
            :param int c_bpartner_id (Parent ID)
            :return: int New AD_User_ID
        """
        fields = [Field('Name',  str(contact.name)),
                  Field('EMail', str(contact.email)),
                  Field('C_BPartner_ID', c_bpartner_id)]

        AD_User_ID = connection.sendRegister(self.create_contact_wst,fields)

        return AD_User_ID

    def createInvoiceAddress(self,connection,address,c_bpartner_id):
        """ Send the customer's Invoice Address to be registered in idempiere
            :param connection_parameter_setting connection
            :param res.partner address
            :param int c_bpartner_id
            :return: int New C_BPartner_Location_ID
        """
        locationFields = [Field('C_Country_ID', '171'),
                  Field('City', str(address.city)),
                  Field('Address1', str(address.street))]

        C_Location_ID = connection.sendRegister(self.create_location_wst,locationFields)

        bpLocationFields= [Field('Name',  str(address.city)+"-"+str(address.street)),
                           Field('C_Location_ID', C_Location_ID),
                           Field('C_BPartner_ID',c_bpartner_id),
                           Field('IsBillTo','Y'),
                           Field('IsShipTo','N')]
        C_BPartner_Location_ID = connection.sendRegister(self.create_bplocation_wst,bpLocationFields)

        return C_BPartner_Location_ID

    def createDeliveryAddress(self,connection,address,c_bpartner_id):
        """ Send the customer's Delivery Address to be registered in idempiere
            :param connection_parameter_setting connection
            :param res.partner address
            :param int c_bpartner_id
            :return: int New C_BPartner_Location_ID
        """
        locationFields = [Field('C_Country_ID', '171'),
                  Field('City', str(address.city)),
                  Field('Address1', str(address.street))]

        C_Location_ID = connection.sendRegister(self.create_location_wst,locationFields)

        bpLocationFields= [Field('Name',  str(address.city)+"-"+str(address.street)),
                           Field('C_Location_ID', C_Location_ID),
                           Field('C_BPartner_ID',c_bpartner_id),
                           Field('IsBillTo','N'),
                           Field('IsShipTo','Y')]
        C_BPartner_Location_ID = connection.sendRegister(self.create_bplocation_wst,bpLocationFields)

        return C_BPartner_Location_ID
