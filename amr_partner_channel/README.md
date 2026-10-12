# Modul `amr_partner_channel`

## Untuk Developer

### 1. Arsitektur
Modul `amr_partner_channel` mengelola kanal komunikasi multi-channel (WhatsApp, Telegram, Email, Instagram, Phone, dll) untuk `res.partner` di Odoo 20. Modul ini menjadi fondasi komunikasi omnichannel dan menghubungkan secara otomatis percakapan ke pipeline penjualan (`crm.lead`).

### 2. Model, Field, dan Relasi
- **`res.partner.channel`**: Model penyimpanan kanal komunikasi.
  - `channel_type`: Selection (`whatsapp`, `telegram`, `email`, `instagram`, `phone`, `line`, `other`).
  - `identifier`: Identifikasi unik kanal (nomor E.164, username Telegram/IG, email).
  - `partner_id`: Many2one ke `res.partner` (cascade delete).
  - `is_primary`: Boolean penanda kanal utama.
  - `active`: Boolean status aktif.
  - `external_id`: Sinkronisasi ID Chatwoot.
- **`res.partner` (Extend)**:
  - `channel_ids`: One2many ke `res.partner.channel`.
- **`crm.lead` (Extend)**:
  - Otomatis melakukan *auto-linking* `partner_id` berdasarkan `phone`, `mobile`, atau `email_from` yang cocok dengan `res.partner.channel`.

### 3. Cara Modul Lain Memakainya
```python
# Mencari partner berdasarkan channel identifier
partner = env['res.partner.channel'].get_partner_by_channel('whatsapp', '+628123456789')
```

### 4. API / Method Publik
- `get_partner_by_channel(channel_type, identifier)`: Mengembalikan record `res.partner` atau kosong.

### 5. Dependensi
- `base`, `mail`, `crm`.

### 6. Konfigurasi
- Tidak memerlukan parameter sistem khusus. Otomatis men-seed channel dari field `mobile` dan `email` saat partner dibuat atau diubah.

### 7. Error Handling
- Validasi input menggunakan normalisasi Unicode NFKD dan pustaka `phonenumbers` untuk format E.164. Pengecualian `ValidationError` dilempar jika format tidak valid.

### 8. Catatan Pola Odoo 20
- Menggunakan dekorator standar Odoo 20 (`@api.model_create_multi`, `@api.constrains`, `@api.depends`).
- Keamanan berbasis ACL dan *Record Rules* (`ir.rule`) untuk isolasi portal user.

## Untuk User

### Menu & Form
- Lokasi menu: **Contacts > Channels** atau langsung di tab **Channel** pada form `res.partner`.
- Form mendukung *editable tree* untuk penambahan kanal secara cepat.

### Alur Kerja Harian
1. Buat atau edit kontak `res.partner`.
2. Buka tab **Channel** untuk melihat atau menambah nomor WhatsApp, Telegram, atau email tambahan.
3. Saat *lead* CRM masuk via chat/inbox, sistem otomatis mencocokkan nomor/email ke `res.partner.channel` dan menautkan *lead* ke partner yang tepat.
