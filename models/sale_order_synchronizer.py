# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,tools, _
from odoo.exceptions import UserError
from connection_parameter_setting import connection_parameter_setting
from customer_setting import customer_setting
from product_setting import product_setting
from sale_order_setting import sale_order_setting
from idempierewsc.request import QueryDataRequest
from idempierewsc.request import CreateDataRequest
from idempierewsc.request import SetDocActionRequest
from idempierewsc.request import CompositeOperationRequest
from idempierewsc.base import LoginRequest
from idempierewsc.enums import WebServiceResponseStatus
from idempierewsc.net import WebServiceConnection
from idempierewsc.base import Field
from idempierewsc.base import Operation
from idempierewsc.enums import DocAction
import traceback

class sale_order_synchronizer():


    def synchronize_to_idempiere(self, order):
        print "synchronize_to_idempiere"
        connection_parameter = order.env['idempiere_synchronizer_so.connection_parameter_setting'].search([('idempiere_login_client_id', '>', '0')], limit=1)
        if connection_parameter.id==False:
            order.toSchedule(_("No Connection Setting"))
            return False
        customer_set = order.env['idempiere_synchronizer_so.customer_setting'].search([('idempiere_web_service_type', '!=', '')], limit=1)
        if customer_set.id==False:
            order.toSchedule(_("No Customer Setting"))
            return False
        product_set = order.env['idempiere_synchronizer_so.product_setting'].search([('idempiere_web_service_type', '!=', '')], limit=1)
        if product_set.id==False:
            order.toSchedule(_("No Product Setting"))
            return False
        saleorder_set = order.env['idempiere_synchronizer_so.sale_order_setting'].search([('idempiere_c_doctypetarget_id', '>', '0')], limit=1)
        if saleorder_set.id==False:
            order.toSchedule(_("No Sale Order Setting"))
            return False

        customerID = customer_set.getCustomerID(connection_parameter,order)
        if customerID == 0:
           customerID =  customer_set.sendCustomer(connection_parameter,order)
        if (customerID>0):
            success = saleorder_set.sendOrder(connection_parameter,customerID,order,product_set)
        else:
            order.toSchedule(_("Unsent Customer"))
            return False

        return success
