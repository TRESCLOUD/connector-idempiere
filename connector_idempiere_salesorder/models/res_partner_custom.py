# -*- coding: utf-8 -*-

from operator import itemgetter
import time

from odoo import api, fields, models, _

#Class inherited from res Partner
class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_policy_selection = [
        ('A', 'Availability'),
        ('F', 'Force'),
        ('L', 'Complete Line'),
        ('M', 'Manual'),
        ('O', 'Complete Order'),
        ('R', 'After Receipt')]

    # Columns
    delivery_policy = fields.Selection(delivery_policy_selection, track_visibility='always',
        help='Allow the user select the delivery policy type to be use in sale order')
    
    @api.multi
    def address_get_idempiere(self, adr_pref=None):
        """ Basado en el metodo address_get del partner, pero sin agregar valores por defecto
        Find contacts/addresses of the right type(s) by doing a depth-first-search
        through descendants within company boundaries (stop at entities flagged ``is_company``)
        then continuing the search at the ancestors that are within the same company boundaries.
        Defaults to partners of type ``'default'`` when the exact type is not found, or to the
        provided partner itself if no type ``'default'`` is found either. """
        adr_pref = set(adr_pref or [])
        if 'contact' not in adr_pref:
            adr_pref.add('contact')
        result = {}
        visited = set()
        for partner in self:
            current_partner = partner
            while current_partner:
                to_scan = [current_partner]
                # Scan descendants, DFS
                while to_scan:
                    record = to_scan.pop(0)
                    visited.add(record)
                    if record.type in adr_pref and not result.get(record.type):
                        if record.parent_id:
                            result[record.type] = record.id
                    if len(result) == len(adr_pref):
                        return result
                    to_scan = [c for c in record.child_ids
                                 if c not in visited
                                 if not c.is_company] + to_scan

                # Continue scanning at ancestor if current_partner is not a commercial entity
                if current_partner.is_company or not current_partner.parent_id:
                    break
                current_partner = current_partner.parent_id

        # default to type 'contact' or the partner itself
        default = result.get('contact', self.id or False)
        for adr_type in adr_pref:
            result[adr_type] = result.get(adr_type) or False
        return result
