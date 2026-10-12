# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    channel_ids = fields.One2many('res.partner.channel', 'partner_id', string='Channels')

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner in partners:
            partner._seed_channels_from_attributes()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if 'mobile' in vals or 'phone' in vals or 'email' in vals or 'x_telegram_id' in vals:
            for partner in self:
                partner._seed_channels_from_attributes()
        return res

    def _seed_channels_from_attributes(self):
        self.ensure_one()
        Channel = self.env['res.partner.channel'].sudo()

        # Seed WhatsApp / phone from mobile
        if self.mobile:
            existing = Channel.search([
                ('partner_id', '=', self.id),
                ('channel_type', '=', 'whatsapp'),
                ('identifier', '=', self.mobile)
            ], limit=1)
            if not existing:
                try:
                    Channel.create({
                        'partner_id': self.id,
                        'channel_type': 'whatsapp',
                        'identifier': self.mobile,
                        'is_primary': True,
                    })
                except Exception:
                    pass

        # Seed Telegram from x_telegram_id if present on partner
        if hasattr(self, 'x_telegram_id') and self.x_telegram_id:
            tg_id = str(self.x_telegram_id).strip()
            if tg_id:
                existing = Channel.search([
                    ('partner_id', '=', self.id),
                    ('channel_type', '=', 'telegram'),
                    ('identifier', '=', tg_id)
                ], limit=1)
                if not existing:
                    try:
                        Channel.create({
                            'partner_id': self.id,
                            'channel_type': 'telegram',
                            'identifier': tg_id,
                            'is_primary': not bool(self.mobile),
                        })
                    except Exception:
                        pass

        # Seed Email
        if self.email:
            em = self.email.strip().lower()
            existing = Channel.search([
                ('partner_id', '=', self.id),
                ('channel_type', '=', 'email'),
                ('identifier', '=', em)
            ], limit=1)
            if not existing:
                try:
                    Channel.create({
                        'partner_id': self.id,
                        'channel_type': 'email',
                        'identifier': em,
                        'is_primary': not bool(self.mobile) and not (hasattr(self, 'x_telegram_id') and self.x_telegram_id),
                    })
                except Exception:
                    pass
