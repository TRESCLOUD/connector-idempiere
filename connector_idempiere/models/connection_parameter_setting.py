# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from idempierewsc.base import LoginRequest
from idempierewsc.net import WebServiceConnection
from idempierewsc.request import CreateDataRequest
from idempierewsc.base import Field
from idempierewsc.request import QueryDataRequest
from idempierewsc.enums import WebServiceResponseStatus
import traceback

# Class responsible for generating the necessary objects for
# the connection with the webservices of the iDempiere server

class connection_parameter_setting(models.Model):
    _name = 'connector_idempiere.connection_parameter_setting'

    idempiere_url = fields.Char('iDempiere URL',required=True)
    idempiere_urls = fields.Char('iDempiere URLs',required=True)
    idempiere_login_client_id = fields.Char('iDempiere AD_Client_ID',required=True)
    idempiere_login_org_id = fields.Char('iDempiere AD_Orge_ID',required=True)
    idempiere_login_role_id = fields.Char('iDempiere AD_Role_ID',required=True)
    idempiere_login_password = fields.Char('iDempiere Password',required=True)
    idempiere_login_user = fields.Char('iDempiere AD_User_ID',required=True)

    def getLogin(self):
        """ Get an object of type LoginRequest used in the authentication of webservices consumed
            :return: (LoginRequest) loging
        """
        login = LoginRequest()
        login.client_id = self.idempiere_login_client_id
        login.role_id = self.idempiere_login_role_id
        login.password = self.idempiere_login_password
        login.user = self.idempiere_login_user
        login.stage =10

        return login

    def getWebServiceConnection(self):
        """ Get an object of type WebServiceConnection used to establish connection with the
            remote webservice through the configured url
            :return: (LoginRequest) loging
        """
        wsc = WebServiceConnection()
        wsc.url = self.idempiere_urls
        wsc.attempts = 3
        wsc.app_name = 'connector_idempiere'

        return wsc

    def getCreateDataRequestWebService(self,webServiceType,fields):
       """ Get an object of type WebService used to send a CreateDataRequest WebService
            :param char webServiceType
            :param Field[] fields
            :return: (CreateDataRequest) WebService
        """
       ws = CreateDataRequest()
       ws.web_service_type = webServiceType
       ws.data_row = fields

       return ws

    def getQueryDataRequestWebService(self,webServiceType,login,filter,limit):
       """ Get an object of type WebService used to read data from iDempiere
            :param char webServiceType
            :param LoginRequest login
            :param Char filter
            :param int limit
            :return: (QueryDataRequest) WebService
        """
       ws = QueryDataRequest()
       ws.web_service_type = webServiceType
       ws.offset = 0
       ws.limit = limit
       ws.login = login
       ws.filter= filter

       return ws

    def getRecordID(self,webServiceType,filter,columnKeyName):
        """ Obtain the idempiere record identifier (C_BPartner_ID) of a customer associated with an odoo sales order
            :param connection_parameter_setting connection
            :param Char filter
            :param Char webServiceType
            :param Char columnKeyName
            :return: iDempiere's RercordID
        """

        ws = self.getQueryDataRequestWebService(webServiceType,self.getLogin(),filter,1)
        wsc = self.getWebServiceConnection()

        recordID = 0 #id en la bdd de idempiere
        try:
            response = wsc.send_request(ws)
            wsc.print_xml_request()
            wsc.print_xml_response()
            if response.status == WebServiceResponseStatus.Error:
                raise UserError(_('Error de conexion iDempiere %s') % response.error_message)
            for row in response.data_set:
                for line in row:
                    if line.column == columnKeyName:
                        recordID = int(line.value)
        except Exception, e:
            raise UserError('Error de conexion iDempiere: '+ str(e))
        return recordID

    def sendRegister(self,webServiceType,fields):
        """ Send the customer to be registered in idempiere
            :param connection_parameter_setting connection
            :param res.partner partner
            :return: int New iDempiere's RercordID
        """
        ws = self.getCreateDataRequestWebService(webServiceType,fields)
        ws.login = self.getLogin()
        wsc = self.getWebServiceConnection()
        recordID = 0
        response = wsc.send_request(ws)
        wsc.print_xml_request()
        wsc.print_xml_response()
        if response.status == WebServiceResponseStatus.Error:
            raise UserError(_('Error de conexion iDempiere %s') % response.error_message)
        recordID = int(response.record_id)
        return recordID