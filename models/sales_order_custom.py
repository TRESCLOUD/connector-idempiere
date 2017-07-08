# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,tools, _
from odoo.exceptions import UserError
from sale_order_synchronizer import sale_order_synchronizer

class sale_order_custom(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        res = super(sale_order_custom, self).action_confirm()
        print ('Synchronizing....')
        synchronizer = sale_order_synchronizer()
        synchronizer.synchronize_to_idempiere(self)

        return res

