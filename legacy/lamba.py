#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @raycast.schemaVersion 1
# @raycast.title Lamba Aç/Kapat
# @raycast.mode silent
# @raycast.packageName Akıllı Ev
# @raycast.icon 💡


# # Bu bilgileri Tuya Overview sayfasından alacaksın
# ACCESS_ID = 
# ACCESS_SECRET =
# ENDPOINT = 
# DEVICE_ID = 

import sys
import io
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# pythonw.exe altında sys.stdout / sys.stderr None olur.
# Önce bunları güvenli hale getiriyoruz, aksi halde print() veya
# herhangi bir kütüphane içi hata loglaması programı sessizce çökertir.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')

from tuya_connector import TuyaOpenAPI
from windows_toasts import WindowsToaster, Toast  # Modern Win11 kütüphanesi

# Scriptin bulunduğu dizindeki .env dosyasını yükle
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

ACCESS_ID = os.getenv("ACCESS_ID", "")
ACCESS_SECRET = os.getenv("ACCESS_SECRET", "")
ENDPOINT = os.getenv("ENDPOINT", "")
DEVICE_ID = os.getenv("DEVICE_ID", "")

openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_SECRET)
openapi.connect()

# 1. Mevcut durumu al
status = openapi.get(f'/v1.0/iot-03/devices/{DEVICE_ID}/status')
current_state = False
for item in status['result']:
    if item['code'] == 'switch_led':
        current_state = item['value']

# 2. Durumu tersine çevir
new_state = not current_state
commands = {'commands': [{'code': 'switch_led', 'value': new_state}]}
openapi.post(f'/v1.0/iot-03/devices/{DEVICE_ID}/commands', commands)

# 3. Duruma göre mesajı belirle
if new_state:
    durum_mesaji = "💡 Lambanız başarıyla açıldı!"
    konsol_mesaji = "Lamba Açıldı"
else:
    durum_mesaji = "🌑 Lambanız kapatıldı!"
    konsol_mesaji = "Lamba Kapatıldı"

# 4. Windows 11 Modern Bildirimi Gönder
toaster = WindowsToaster('Akıllı Ev')
new_toast = Toast()
new_toast.text_fields = [durum_mesaji]
toaster.show_toast(new_toast)

print(konsol_mesaji)

# pythonw altında script bildirim gösterilmeden hemen kapanabilir
# çünkü toast'ın gösterilmesi arka planda asenkron işliyor.
# Bu yüzden kısa bir süre bekletiyoruz.
time.sleep(3)