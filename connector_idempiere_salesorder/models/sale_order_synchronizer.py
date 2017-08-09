# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,tools, _
from odoo.exceptions import UserError

from sale_order_setting import sale_order_setting

class sale_order_synchronizer():


    def synchronize_to_idempiere(self, order):
        """ Send the odoo's sales order to be registered in idempiere
            :param sale.order order
        """
        print "synchronize_to_idempiere"
        connection_parameter = order.env['connector_idempiere.connection_parameter_setting'].search([('idempiere_login_client_id', '>', '0')], limit=1)
        if connection_parameter.id==False:
            order.toSchedule(_("No Connection Setting"))
            return False
        customer_set = order.env['connector_idempiere_bpartner.customer_setting'].search([('read_bpartner_wst', '!=', '')], limit=1)
        if customer_set.id==False:
            order.toSchedule(_("No Customer Setting"))
            return False
        product_set = order.env['connector_idempiere_product.product_setting'].search([('read_product_wst', '!=', '')], limit=1)
        if product_set.id==False:
            order.toSchedule(_("No Product Setting"))
            return False
        saleorder_set = order.env['connector_idempiere_salesorder.sale_order_setting'].search([('idempiere_c_doctypetarget_id', '>', '0')], limit=1)
        if saleorder_set.id==False:
            order.toSchedule(_("No Sale Order Setting"))
            return False
        success_id = order.sendOrder(connection_parameter,order,product_set,saleorder_set,customer_set)
        return success_id
