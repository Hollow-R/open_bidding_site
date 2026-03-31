# OBID - Online Ihale / Bidding Sistemi

Bu proje Django tabanli, grup ve menu yetkisi ile calisan bir ihale uygulamasidir.

## Teknik Yapi

- Python 3.8+
- Django
- Django REST Framework
- Django Allauth (OAuth)
- Bootstrap
- DevExtreme DataGrid

## Kurulum

1. Sanal ortami olustur ve aktif et:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Paketleri yukle:

```bash
pip install -r requirements.txt
```

3. Veritabani migrationlarini calistir:

```bash
python manage.py migrate
```

4. Uygulamayi baslat:

```bash
python manage.py runserver
```

## OAuth (GitHub) Kurulumu

1. GitHub Developer Settings uzerinden OAuth App olustur.
2. Callback URL:
   - `http://127.0.0.1:8000/accounts/github/login/callback/`
3. Django Admin > Social Applications altindan GitHub provider icin `Client ID` ve `Secret` gir.
4. `Site` olarak `example.com` secili olmali (`SITE_ID=1`).

## Kullanici ve Yetki Modeli

- Menuler `Menu` tablosunda tutulur.
- Grup-menu iliskisi `GroupMenuPermission` ile yonetilir.
- Kullanici bir menuyu gorse bile backend tarafinda ayrica yetki kontrolu vardir.
- Yeni olusan normal kullanicilar otomatik olarak `Musteri` grubuna atanir.

## Notlar

- Gelistirme ortami icin `DEBUG=True` kullanilmistir.
- Uretim ortamina geciste `SECRET_KEY`, `ALLOWED_HOSTS`, guvenlik ve OAuth ayarlari tekrar duzenlenmelidir.
