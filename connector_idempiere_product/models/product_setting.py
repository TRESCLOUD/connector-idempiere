# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from idempierewsc.request import QueryDataRequest
from idempierewsc.net import WebServiceConnection
from idempierewsc.enums import WebServiceResponseStatus

import traceback


#Configuration class of basic parameters for Products synchronization
class product_setting(models.Model):
    _name = 'connector_idempiere_product.product_setting'

    odoo_key_column_name = fields.Char('Odoo Key Column Name',required=True)
    idempiere_key_column_name = fields.Char('iDempiere Key Column Name',required=True)
    idempiere_web_service_type = fields.Char('iDempiere WebService Type',required=True)
    idempiere_filter = fields.Text('iDempiere WebService Filter',required=False)
    limit = fields.Integer('Limit',default=1)

    #Get the idempiere record identifier (M_Product_ID) of a Product associated with an odoo sales order
    def getProductID(self,connection_parameter,productvalue):

        ws = QueryDataRequest()
        ws.web_service_type = self.idempiere_web_service_type
        ws.offset = 0
        ws.limit = 1
        ws.login = connection_parameter.getLogin()

        ws.filter= self.idempiere_key_column_name +" = '" +str(productvalue)+"'"

        wsc = connection_parameter.getWebServiceConnection()

        productID = 0
        try:
            response = wsc.send_request(ws)
            wsc.print_xml_request()
            wsc.print_xml_response()

            if response.status == WebServiceResponseStatus.Error:
                traceback.print_exc()
            else:
                for row in response.data_set:
                    productID = int(row[0].value)

        except:
            traceback.print_exc()

        return productID

    def get_odoo_product(self,productvalue):
        product = self.env['product.product'].search([(self.odoo_key_column_name, '=', str(productvalue))], limit=1)
        return product

    @api.one
    def getproducts_from_idempiere(self):
        created_count = 0
        updated_count = 0
        connection_parameter = self.env['connector_idempiere.connection_parameter_setting'].search([('idempiere_login_client_id', '>', '0')], limit=1)
        if connection_parameter.id==False:
            return {
                "warning":{
                "title": _("Alert"),
                "message": _("No Connection Setting"),
                },
            }

        ws = QueryDataRequest()
        ws.web_service_type = 'QueryProduct'
        ws.offset = 0
        ws.limit = self.limit
        ws.login = connection_parameter.getLogin()
        ws.filter= self.idempiere_filter
        wsc = connection_parameter.getWebServiceConnection()

        try:
            response = wsc.send_request(ws)
            if response.status == WebServiceResponseStatus.Error:
                traceback.print_exc()
            else:
                for row in response.data_set:
                    values = {}
                    for field in row:
                        column = str(field.column).lower()

                        if str(column)==self.odoo_key_column_name:
                            value = str(field.value)
                        if str(column)=='category_name':
                            column = 'categ_id'
                            field.value = self.getCateg_id(str(field.value))
                        if str(column)=='rate_taxe':
                            column = 'taxes_id'
                            field.value = self.getTax_id(str(field.value))
                        values[column] = str(field.value)


                    product = self.get_odoo_product(value)

                    if not product:
                        product = self.env['product.product'].create(values)
                        created_count = created_count + 1
                    else:
                        product.name = values['name']
                        product.list_price = values['list_price']
                        updated_count = updated_count + 1
        except:
            traceback.print_exc()

        return {
                "warning":{
                "title": _("Alert"),
                "message": _("Created Products : " + str(created_count) + ", Updated Products: "+  str(updated_count)),
                },
            }

    def getCateg_id(self,category_name):
        return 1
    def getTax_id(self,category_name):
        return 1