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
        #para el partner usamos la cedula/ruc o el codigo parametrizado
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
        #si el nombre coincide exactamente, y si el parent_id apunta al al mismo.
        filter = "Name = '" + str(contact.name) \
                 + "' AND C_BPartner_ID = "+str(c_bpartner_id) \
                 + " AND IsActive = 'Y'"
        AD_User_ID = connection.getRecordID(self.read_contact_wst,filter,'AD_User_ID')
        return AD_User_ID

    def getInvoiceAddressID(self,connection,address,c_bpartner_id):
        """ Obtain the idempiere record identifier (C_BPartner_Location) of a Invoice customer'address associated with an odoo sales order
            :param connection_parameter_setting connection
            :param res.partner address (Type = Delivery)
            :param int c_bpartner_id
            :return: iDempiere's AD_User_ID of Contact
        """
        filter = "Name = '" + str(address.name) \
                 + "' AND C_BPartner_ID = "+str(c_bpartner_id) \
                 + " AND IsBillTo = 'Y'" \
                 + " AND IsActive = 'Y'"
        C_BPartner_Location_ID = connection.getRecordID(self.read_bplocation_wst,filter,'C_BPartner_Location_ID')
        return C_BPartner_Location_ID

    def getDeliveryAddressID(self,connection,address,c_bpartner_id):
        """ Obtain the idempiere record identifier (C_BPartner_Location) of a Delivery customer'address associated with an odoo sales order
            :param connection_parameter_setting connection
            :param res.partner address (Type = Delivery)
            :param int c_bpartner_id
            :return: iDempiere's AD_User_ID of Contact
        """
        filter = "Name = '" + str(address.name) \
                 + "' AND C_BPartner_ID = "+str(c_bpartner_id) \
                 + " AND IsShipTo = 'Y'" \
                 + " AND IsActive = 'Y'"
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
                  Field('TaxID', str(partner.vat)),
                  Field('C_BP_Group_ID', str(partner.partner_category_id.c_bp_group_id)), 
                  Field('SalesRep_ID', str(partner.user_id.ad_user_id)),
                  ]
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
                  Field('Description', str(contact.function or '')),
                  Field('EMail', str(contact.email or '')),
                  Field('Phone', str(contact.phone or '')),
                  Field('Phone2', str(contact.mobile or '')),
                  Field('Comments', str(contact.comment or '')),
                  Field('C_BPartner_ID', c_bpartner_id),
                  ]                      
        AD_User_ID = connection.sendRegister(self.create_contact_wst,fields)

        return AD_User_ID

    def createAddress(self,connection,address,c_bpartner_id):
        """ Send the customer's Invoice Address to be registered in idempiere
            :param connection_parameter_setting connection
            :param res.partner address
            :param int c_bpartner_id
            :return: int New C_BPartner_Location_ID
        """
        locationFields = [
                  Field('Address1', str(address.street or '')),
                  Field('Address2', str(address.street2 or '')),
                  Field('City', str(address.city or '')),
                  Field('Postal', str(address.zip or '')),
                  ]
        if address.city_id:
            if not address.city_id.C_City_ID:
                raise UserError(_('Error iDempiere: La ciudad %s no tiene un id relacionado en iDempiere') % address.city_id.name)
            locationFields.append(Field('C_City_ID', str(address.city_id.C_City_ID)))
        if address.state_id:
            if not address.state_id.C_Region_ID:
                raise UserError(_('Error iDempiere: La provincia %s no tiene un id relacionado en iDempiere') % address.state_id.name)
            locationFields.append(Field('C_Region_ID', str(address.state_id.C_Region_ID)))
        if address.country_id:
            if not address.country_id.C_Country_ID:
                raise UserError(_('Error iDempiere: La ciudad %s no tiene un id relacionado en iDempiere') % address.country_id.name)
            locationFields.append(Field('C_Country_ID', str(address.country_id.C_Country_ID)))
        locationFields.append(Field('AD_Client_ID', str(connection.idempiere_login_client_id)))
        C_Location_ID = connection.sendRegister(self.create_location_wst,locationFields)
        bpLocationFields= [Field('Name',  str(address.name)),
                           Field('C_Location_ID', C_Location_ID),
                           Field('C_BPartner_ID',c_bpartner_id),
                           Field('IsBillTo','Y'), #Ambos en Y porque Odoo no diferencia
                           Field('IsShipTo','Y')]
        C_BPartner_Location_ID = connection.sendRegister(self.create_bplocation_wst,bpLocationFields)
        return C_BPartner_Location_ID
