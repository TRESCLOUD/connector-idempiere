# -*- coding: utf-8 -*-

from operator import itemgetter
import time

from odoo import api, fields, models, _


class Country(models.Model):
    _inherit = 'res.country'

    # Columns
    C_Country_ID = fields.Integer('ID from Idempiere',
                              required=False,
                              help='ID in the database of idempiere')    


class CountryState(models.Model):
    _inherit = 'res.country.state'
    
    C_Region_ID = fields.Integer('ID from Idempiere',
                              required=False,
                              help='ID in the database of idempiere')
    
    
class ResCity(models.Model):
    _inherit = 'res.city'
    
    C_City_ID = fields.Integer('ID from Idempiere',
                              required=False,
                              help='ID in the database of idempiere')
    