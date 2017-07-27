# -*- coding: utf-8 -*-

from operator import itemgetter
import time

from odoo import api, fields, models, _

#Class inherited from res Partner
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Columns
    delivery_policy = fields.Selection([
        ('A', 'Availability'),
        ('F', 'Force'),
        ('L', 'Complete Line'),
        ('M', 'Manual'),
        ('O', 'Complete Order'),
        ('R', 'After Receipt'),
        ], track_visibility='always',
        help='Allow the user select the delivery policy type to be use in sale order')
    