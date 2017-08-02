# -*- coding: utf-8 -*-

from operator import itemgetter
import time

from odoo import api, fields, models, _

#Class inherited from res Partner
class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

        # Columns
    C_PaymentTerm_ID = fields.Integer('ID Payment Term from iDempiere',
                              required=True,
                              default='0',
                              help='The terms of Payment C_PaymentTerm_ID')
