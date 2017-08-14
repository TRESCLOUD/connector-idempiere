# -*- coding: utf-8 -*-

from operator import itemgetter
import time

from odoo import api, fields, models, _

#Class inherited from res Partner
class ResUsers(models.Model):
    _inherit = 'res.users'

    # Columns
    ad_user_id = fields.Integer('ID from Idempiere',
                              copy=False,
                              required=False,
                              help='ID in the database of idempiere  (ad_user_id)')
    

