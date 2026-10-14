# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestPartnerChannel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'phone': '+628123456789',
            'email': 'test@example.com',
        })

    def test_01_channel_creation_and_seeding(self):
        """Test automatic channel seeding from partner phone/email"""
        channels = self.partner.channel_ids
        self.assertTrue(len(channels) >= 1)
        
        # Test get_partner_by_channel helper
        found_partner = self.env['res.partner.channel'].get_partner_by_channel('whatsapp', '+628123456789')
        self.assertEqual(found_partner, self.partner)

    def test_02_validation_and_sanitization(self):
        """Test E.164 and Unicode normalization on identifiers"""
        Channel = self.env['res.partner.channel']
        
        # Valid telegram with @ prefix stripping
        ch = Channel.create({
            'partner_id': self.partner.id,
            'channel_type': 'telegram',
            'identifier': '@John_Doe123',
        })
        self.assertEqual(ch.identifier, 'john_doe123')

        # Invalid telegram format should raise ValidationError
        with self.assertRaises(ValidationError):
            Channel.create({
                'partner_id': self.partner.id,
                'channel_type': 'telegram',
                'identifier': 'abc', # Too short
            })

    def test_03_crm_lead_linking(self):
        """Test automatic lead linking via channel identifier"""
        lead = self.env['crm.lead'].create({
            'name': 'Test Lead via WA',
            'phone': '+628123456789',
        })
        self.assertEqual(lead.partner_id, self.partner)
