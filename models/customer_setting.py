# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class customer_setting(models.Model):
    _name = 'idempiere_synchronizer_so.customer_setting'

    odoo_key_column_name = fields.Char('Odoo Key Column Name',required=True)
    idempiere_key_column_name = fields.Char('iDempiere Key Column Name',required=True)
    idempiere_web_service_type = fields.Char('iDempiere WebService Type',required=True)