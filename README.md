# SIWALAN – Si Penjadwalan

Sistem manajemen jadwal perkuliahan berbasis Django.

## Instalasi

```bash
git clone <repo-url>
cd scheduling
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Fitur

- Generate jadwal otomatis 1 semester
- Validasi konflik: dosen, ruangan, kelas, kapasitas, hari libur
- Workflow reschedule dengan approval admin
- Dashboard dosen + API cek ruangan kosong real-time
