# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from idempierewsc.request import QueryDataRequest
from idempierewsc.net import WebServiceConnection
from idempierewsc.enums import WebServiceResponseStatus
import time
import datetime
import traceback

#forzamos la codificacion a utf-8
#util para conversiones a string realizadas en el documento
import sys
from mx.DateTime.DateTime import today
reload(sys)
sys.setdefaultencoding('utf-8')



#Configuration class of basic parameters for Products synchronization
class product_setting(models.Model):
    _name = 'connector_idempiere_product.product_setting'

    odoo_key_column_name = fields.Char('Odoo Key Column Name',required=True)
    idempiere_key_column_name = fields.Char('iDempiere Key Column Name',required=True)
    read_product_wst = fields.Char('WST Read a Product',required=True,help='Only Read a register, not create or update data')
    get_product_wst = fields.Char('WST get Products',required=True,help='Web Service Type for get a list of Products and register in odoo')
    idempiere_filter = fields.Char('iDempiere WebService Filter',required=False,help='')
    limit = fields.Integer('Limit',default=1)
    result = fields.Text('Result')

    def getProductID(self,connection_parameter,productvalue):
        """ Get the idempiere record identifier (M_Product_ID) of a Product associated with an odoo sales order
            :param connection_parameter_setting connection_parameter
            :param String productvalue
            :return: M_Product_ID of idempiere
        """
        ws = QueryDataRequest()
        ws.web_service_type = self.read_product_wst
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
        """ Get odoo product from env
            :param string productvalue
            :return: odoo product or False
        """
        product = self.env['product.template'].search([(self.odoo_key_column_name, '=', str(productvalue))], limit=1)
        return product

    @api.one
    def getproducts_from_idempiere(self):
        """ Create or Update odoo products from idempiere product Through webservice with idempiere_filter applied
        """
        created_count = 0
        updated_products_ids = []
        start_time = time.time()
        connection_parameter = self.env['connector_idempiere.connection_parameter_setting'].search([('idempiere_login_client_id', '>', '0')], limit=1)
        if connection_parameter.id==False:
            return {
                "warning":{
                "title": _("Alert"),
                "message": _("No Connection Setting"),
                },
            }
        ws = QueryDataRequest()
        ws.web_service_type = self.get_product_wst
        ws.offset = 0
        ws.limit = self.limit
        ws.login = connection_parameter.getLogin()
        ws.filter= self.idempiere_filter
        wsc = connection_parameter.getWebServiceConnection()
        response = wsc.send_request(ws)
        wsc.print_xml_request()
        wsc.print_xml_response()
        if response.status == WebServiceResponseStatus.Error:
            raise UserError(_('Error iDempiere: %s') % response.error_message)
        old_products_from_idempiere = self.env['product.template'].search([('m_product_id', '>', 0)]) #los productos de idempiere tienen el id guardado aqui
        old_products_from_idempiere_ids = old_products_from_idempiere.mapped('id')
        for row in response.data_set:
            values = {}
            for field in row:
                column = str(field.column).lower()
                if field.value == 'MAT-456456':
                    a=1
                if str(column)==self.odoo_key_column_name:
                    key = str(field.value)
                if str(column)=='category_name':
                    column = 'categ_id'
                    field.value = self.getCateg_id(str(field.value)) #TODO: Agregar el id de la categoria a Odoo para no buscar por nombre
                if str(column)=='c_uom_id': #mapeamos el id de unidad de medida de idempiere al id de Odoo
                    uom = self.env['product.uom'].search([['c_uom_id', '=', field.value], ['active', '=', True]],limit=1)
                    if not uom:
                        raise UserError(_('Error iDempiere: En Odoo debe configurar una unidad de medida equivalente a idempiere, con c_uom_id =%s') % str(field.value))
                    
                    column = 'uom_id'
                    field.value = uom.id
                values[column] = field.value
            values['active'] = True #los productos importados de idempiere son activos (la vista product_product ya considera esto)
            if values['uom_id']:
                values['uom_po_id'] = values['uom_id'] #seteamos la unidad de medida de compra igual a la de venta
            values['invoice_policy'] = 'delivery' #para no tener que generar la factura
            values['type'] = 'consu' #para no tener alertas por falta de inventario
            product = self.get_odoo_product(key)
            if not product:
                product = self.env['product.template'].create(values)
                created_count = created_count + 1
            else:
                product.write(values)
                updated_products_ids.append(product.id)
        #productso deprecados
        deprecated_product_ids = [item for item in old_products_from_idempiere_ids if item not in updated_products_ids] 
        deprecated_products = self.env['product.template'].search([('id', 'in', deprecated_product_ids)])
        deprecated_products.write({'active': False})
        end_time = time.time()
        message= "Last Processing Date: " + str(datetime.datetime.now()) + " UTC"\
                 "\nCreated Products: " + str(created_count) + \
                 "\nUpdated Products: "+  str(len(updated_products_ids)) + \
                 "\nDeprecated Products: "+  str(len(deprecated_product_ids)) + \
                 "\nElapsed Time: " + str(round(end_time - start_time,2)) + " segundos"
        print message #TODO Cambiar por log
        self.result = message
        return {
                "warning":{
                "title": _("Alert"),
                "message": message,
                },
            }

    def getCateg_id(self,category_name):
        """ Get the categ_id of odoo with name = category_name
            :param string category_name
            :return: id of product category
        """
        catetory = self.env['product.category'].search([("name", "=", str(category_name))], limit=1)
        if catetory:
            return catetory.id
        return False
