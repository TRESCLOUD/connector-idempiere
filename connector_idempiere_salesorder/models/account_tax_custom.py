# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,tools, _

#Class inherited from Account Tax to assign the id value from idempiere
class AccountTax(models.Model):
    _inherit = "account.tax"

    # Columns
    C_Tax_ID = fields.Integer('ID tax from Idempiere',
                              required=True,
                              help='Store the tax id from Idempiere')