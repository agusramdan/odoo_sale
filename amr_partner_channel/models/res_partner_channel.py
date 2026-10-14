# -*- coding: utf-8 -*-
import re
import unicodedata
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

try:
    import phonenumbers
except ImportError:
    phonenumbers = None


class ResPartnerChannel(models.Model):
    _name = 'res.partner.channel'
    _description = 'Partner Communication Channel'
    _order = 'partner_id, is_primary desc, id'

    name = fields.Char('Channel Name', compute='_compute_name', store=True)
    channel_type = fields.Selection([
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('email', 'Email'),
        ('instagram', 'Instagram'),
        ('phone', 'Phone'),
        ('line', 'LINE'),
        ('other', 'Other'),
    ], string='Tipe Channel', required=True, index=True, default='whatsapp')
    
    identifier = fields.Char('Identifier', required=True, index=True,
        help="Nomor WA/telepon (E.164), username Telegram, alamat email, dll")
    partner_id = fields.Many2one('res.partner', string='Partner', required=True,
        ondelete='cascade', index=True)
    is_primary = fields.Boolean('Utama', default=False)
    active = fields.Boolean('Aktif', default=True)
    external_id = fields.Char('External ID (Chatwoot)', help="ID contact Chatwoot utk sinkron")
    metadata = fields.Json('Metadata')
    created_at = fields.Datetime('Dibuat', default=fields.Datetime.now, readonly=True)
    last_sync_at = fields.Datetime('Sync Terakhir', readonly=True)

    _sql_constraints = [
        ('identifier_type_active_uniq', 'UNIQUE (channel_type, identifier, active)',
         'Identifier untuk tipe channel ini sudah terdaftar dan aktif!'),
    ]

    @api.depends('channel_type', 'identifier')
    def _compute_name(self):
        for record in self:
            ct = dict(self._fields['channel_type'].selection).get(record.channel_type, record.channel_type or '')
            record.name = f"{ct}: {record.identifier}" if record.identifier else ct

    @api.constrains('channel_type', 'identifier')
    def _validate_identifier(self):
        for record in self:
            if not record.identifier:
                continue
            cleaned = record._sanitize_and_validate(record.channel_type, record.identifier)
            if cleaned != record.identifier:
                record.identifier = cleaned

    def _sanitize_and_validate(self, channel_type, identifier):
        # M-02: Unicode NFKD normalization
        norm_id = unicodedata.normalize('NFKD', identifier).encode('ascii', 'ignore').decode('ascii').strip()
        
        if channel_type == 'telegram':
            # Remove leading @ if present
            if norm_id.startswith('@'):
                norm_id = norm_id[1:]
            if not re.match(r'^[a-zA-Z0-9_]{4,32}$', norm_id):
                raise ValidationError(_("Username Telegram tidak valid (4-32 karakter alfanumerik dan underscore): %s") % identifier)
            return norm_id.lower()
            
        elif channel_type == 'email':
            email_val = identifier.strip().lower()
            if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email_val):
                raise ValidationError(_("Format alamat email tidak valid: %s") % identifier)
            return email_val
            
        elif channel_type in ('whatsapp', 'phone'):
            if phonenumbers:
                try:
                    # Parse assuming Indonesian context (+62) if starts with 0 or 62
                    raw = identifier.strip()
                    if raw.startswith('0'):
                        raw = '+62' + raw[1:]
                    elif not raw.startswith('+'):
                        raw = '+' + raw
                    parsed = phonenumbers.parse(raw, "ID")
                    if not phonenumbers.is_valid_number(parsed):
                        raise ValidationError(_("Nomor telepon/WhatsApp tidak valid: %s") % identifier)
                    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                except Exception as e:
                    if isinstance(e, ValidationError):
                        raise e
                    # Fallback basic regex if libphonenumber fails
                    if not re.match(r'^\+?[1-9]\d{1,14}$', identifier.strip()):
                        raise ValidationError(_("Format nomor E.164 tidak valid: %s") % identifier)
            else:
                # Basic E.164 check without libphonenumber
                val = identifier.strip()
                if val.startswith('0'):
                    val = '+62' + val[1:]
                elif not val.startswith('+'):
                    val = '+' + val
                if not re.match(r'^\+[1-9]\d{1,14}$', val):
                    raise ValidationError(_("Format nomor telepon E.164 tidak valid: %s") % identifier)
                return val
        
        elif channel_type == 'instagram':
            if norm_id.startswith('@'):
                norm_id = norm_id[1:]
            if not re.match(r'^[a-zA-Z0-9._]{1,30}$', norm_id):
                raise ValidationError(_("Username Instagram tidak valid: %s") % identifier)
            return norm_id.lower()
            
        return identifier.strip()

    @api.model
    def get_partner_by_channel(self, channel_type, identifier):
        """Helper for CRM lead linking and NATS commands (§9.3)"""
        if not channel_type or not identifier:
            return self.env['res.partner']
        # Sanitize input first
        try:
            dummy = self.new({'channel_type': channel_type, 'identifier': identifier})
            clean_id = dummy._sanitize_and_validate(channel_type, identifier)
        except Exception:
            clean_id = identifier.strip()

        channel = self.search([
            ('channel_type', '=', channel_type),
            ('identifier', '=', clean_id),
            ('active', '=', True)
        ], limit=1)
        return channel.partner_id if channel else self.env['res.partner']

    @api.model_create_multi
    def create(self, vals_list):
        # K-01: Mass assignment check for portal users
        if self.env.user.has_group('base.group_portal') and not self.env.user.has_group('base.group_system'):
            for vals in vals_list:
                if vals.get('partner_id') and vals.get('partner_id') != self.env.user.partner_id.id:
                    raise ValidationError(_("Anda tidak diizinkan membuat kanal untuk partner lain."))
                vals['is_primary'] = False # Portal user cannot set primary directly without verification
        
        records = super().create(vals_list)
        for rec in records:
            if rec.is_primary:
                # Ensure only one primary per type per partner
                self.search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('channel_type', '=', rec.channel_type),
                    ('id', '!=', rec.id),
                    ('is_primary', '=', True)
                ]).write({'is_primary': False})
        return records

    def write(self, vals):
        # K-01: Portal user protection against IDOR and mass assignment
        if self.env.user.has_group('base.group_portal') and not self.env.user.has_group('base.group_system'):
            for rec in self:
                if rec.partner_id.id != self.env.user.partner_id.id:
                    raise ValidationError(_("Akses ditolak: Bukan kanal Anda."))
            # Whitelist allowed fields for portal users: identifier, metadata, active
            forbidden = set(vals.keys()) - {'identifier', 'metadata', 'active', 'name'}
            if forbidden:
                raise ValidationError(_("Modifikasi field %s tidak diizinkan untuk portal user.") % ', '.join(forbidden))
                
        res = super().write(vals)
        if vals.get('is_primary'):
            for rec in self:
                if rec.is_primary:
                    self.search([
                        ('partner_id', '=', rec.partner_id.id),
                        ('channel_type', '=', rec.channel_type),
                        ('id', '!=', rec.id),
                        ('is_primary', '=', True)
                    ]).write({'is_primary', False})
        return res
