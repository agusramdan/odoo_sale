{
    'name': 'AMR Partner Communication Channels',
    'version': '20.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Multi-channel communication management for partners and CRM lead linking',
    'description': '''
Manages multiple communication channels (WhatsApp, Telegram, Email, Instagram, Phone, etc.) for res.partner,
with E.164 normalization, Unicode validation, portal security isolation, and CRM lead integration.
    ''',
    'author': 'Agus Ramdan',
    'website': 'https://hermescantik.biz.id',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'security/res_partner_channel_security.xml',
        'views/res_partner_channel_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
