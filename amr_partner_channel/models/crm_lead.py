# -*- coding: utf-8 -*-
from odoo import models, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        # §9.2: Auto-link partner by channel identifier if phone/email/mobile or custom channel context is passed
        if not vals.get('partner_id'):
            Channel = self.env['res.partner.channel']
            partner = self.env['res.partner']
            
            # Check phone / mobile
            phone_val = vals.get('phone') or vals.get('mobile')
            if phone_val and not partner:
                partner = Channel.get_partner_by_channel('whatsapp', phone_val)
                if not partner:
                    partner = Channel.get_partner_by_channel('phone', phone_val)
            
            # Check email
            if not partner and vals.get('email_from'):
                partner = Channel.get_partner_by_channel('email', vals.get('email_from'))
                
            if partner:
                vals['partner_id'] = partner.id
                
        return super().create(vals)
