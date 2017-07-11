# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from idempierewsc.base import LoginRequest
from idempierewsc.net import WebServiceConnection


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

    #Get an object of type LoginRequest used in the authentication of webservices consumed
    def getLogin(self):

        login = LoginRequest()
        login.client_id = self.idempiere_login_client_id
        login.role_id = self.idempiere_login_role_id
        login.password = self.idempiere_login_password
        login.user = self.idempiere_login_user
        login.stage =10

        return login

    #Get an object of type WebServiceConnection used to establish connection with the
    #  remote webservice through the configured url
    def getWebServiceConnection(self):
        wsc = WebServiceConnection()
        wsc.url = self.idempiere_urls
        wsc.attempts = 3
        wsc.app_name = 'connector_idempiere'

        return wsc