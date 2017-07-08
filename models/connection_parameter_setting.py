# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class connection_parameter_setting(models.Model):
    _name = 'idempiere_synchronizer_so.connection_parameter_setting'

    idempiere_url = fields.Char('iDempiere URL',required=True)
    idempiere_urls = fields.Char('iDempiere URLs',required=True)
    idempiere_login_client_id = fields.Char('iDempiere AD_Client_ID',required=True)
    idempiere_login_org_id = fields.Char('iDempiere AD_Orge_ID',required=True)
    idempiere_login_role_id = fields.Char('iDempiere AD_Role_ID',required=True)
    idempiere_login_password = fields.Char('iDempiere Password',required=True)
    idempiere_login_user = fields.Char('iDempiere AD_User_ID',required=True)