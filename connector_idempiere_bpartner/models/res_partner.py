# -*- coding: utf-8 -*-

from operator import itemgetter
import time

from odoo import api, fields, models, _

#Class inherited from res Partner
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Columns
    C_Idempiere_ID = fields.Integer('ID from Idempiere',
                              required=False,
                              help='ID in the database of idempiere')    

