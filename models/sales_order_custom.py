# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,tools, _
from odoo.exceptions import UserError
from sale_order_synchronizer import sale_order_synchronizer

class sale_order_custom(models.Model):
    _inherit = "sale.order"

    scheduled = fields.Boolean('Scheduled for later sync',default=False)
    sync_message = fields.Char('Sync message',default='')

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        res = super(sale_order_custom, self).action_confirm()
        print ('Synchronizing....')
        synchronizer = sale_order_synchronizer()
        success = synchronizer.synchronize_to_idempiere(self)

        if success==False:
            message_body = "\n\n".join(self.sync_message)
            self.message_post(body=message_body, subject="Error")

        return res

    def toSchedule(self,message):
        if len(str(self.sync_message)) > 0:
            self.sync_message = str(self.sync_message) + " " +str(message)
        else:
            self.sync_message = str(message)
        self.scheduled = True

        return {
                "warning":{
                "title": _("Alert"),
                "message": self.sync_message,
                },
        }
