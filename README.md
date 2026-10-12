# odoo_sale

Addons **Odoo 20 (native)** untuk domain Sales.

> Bukan hasil migrasi — dikembangkan langsung untuk Odoo 20.

## Standar yang berlaku
- Dokumentasi: mengikuti `TEMPLATE-addon-readme.md` (Developer + User) — lihat project ODOODOC
- Git: branch per code task, PR ke `main` (dilarang push langsung)
- Deploy target: Odoo 20 CANTIK (VPS Sumopod)

## Struktur
```
odoo_sale/
├── README.md
└── <addon>/          # satu folder per addon
    ├── __manifest__.py   (version: 20.0.x.y.z)
    ├── README.md
    ├── models/
    ├── views/
    ├── security/
    ├── wizard/ (opsional)
    └── tests/
```

## Addons
(belum ada — tambahkan sesuai kebutuhan sales)
