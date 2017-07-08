# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from idempierewsc.request import QueryDataRequest
from idempierewsc.net import WebServiceConnection
from idempierewsc.enums import WebServiceResponseStatus

import traceback

class product_setting(models.Model):
    _name = 'idempiere_synchronizer_so.product_setting'

    odoo_key_column_name = fields.Char('Odoo Key Column Name',required=True)
    idempiere_key_column_name = fields.Char('iDempiere Key Column Name',required=True)
    idempiere_web_service_type = fields.Char('iDempiere WebService Type',required=True)

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
