#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @raycast.schemaVersion 1
# @raycast.title Lamba Aç/Kapat (Yerel)
# @raycast.mode silent
# @raycast.packageName Akıllı Ev
# @raycast.icon 💡

import sys
import io
import os
import json
import time
from bulb_controller import TuyaBulbController

# pythonw.exe altında sys.stdout / sys.stderr None olur.
# Önce bunları güvenli hale getiriyoruz, aksi halde print() programı çökertebilir.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
elif hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')

# Windows Modern Bildirim Desteği (Win 10/11)
try:
    from windows_toasts import WindowsToaster, Toast
    HAS_WINDOWS_TOASTS = True
except ImportError:
    HAS_WINDOWS_TOASTS = False

def send_notification(message, title='Akıllı Ev'):
    """Windows bildirim merkezine modern bildirim gönderir."""
    if not HAS_WINDOWS_TOASTS:
        return
    try:
        toaster = WindowsToaster(title)
        toast = Toast()
        toast.text_fields = [message]
        toaster.show_toast(toast)
        # Windows toast asenkron işlendiği için script kapanmadan önce kısa bekleme
        time.sleep(1)
    except Exception:
        pass

def print_help():
    print("""
Kullanım: python main.py <komut> [parametreler]

Komutlar:
  on                : Ampulü açar
  off               : Ampulü kapatır
  toggle            : Açık ise kapatır, kapalı ise açar (Varsayılan)
  cycle             : Renkleri sırayla değiştirir (RGB Cycle)
  status            : Ampulün mevcut durumunu gösterir
  bright <1-100>    : Parlaklığı ayarlar (Örn: python main.py bright 75)
  temp <0-100>      : Beyaz renk sıcaklığını ayarlar (0=Sıcak/Sarı, 100=Soğuk/Beyaz)
  rgb <r> <g> <b>   : RGB rengi ayarlar (Örn: python main.py rgb 255 0 0)
  white             : Beyaz moda geçer
""")

def main():
    if len(sys.argv) < 2:
        cmd = 'toggle'
    else:
        cmd = sys.argv[1].lower()

    if cmd in ['-h', '--help', 'help']:
        print_help()
        return

    try:
        bulb = TuyaBulbController()
    except Exception as e:
        print(f"Hata: {e}")
        send_notification(f"⚠️ Hata: {e}")
        return

    try:
        if cmd == 'on':
            bulb.turn_on()
            print("Ampul AÇILDI")
            send_notification("💡 Lambanız başarıyla açıldı!")
        elif cmd == 'off':
            bulb.turn_off()
            print("Ampul KAPATILDI")
            send_notification("🌑 Lambanız kapatıldı!")
        elif cmd == 'toggle':
            is_now_on = bulb.toggle()
            if is_now_on:
                print("Ampul AÇILDI")
                send_notification("💡 Lambanız başarıyla açıldı!")
            else:
                print("Ampul KAPATILDI")
                send_notification("🌑 Lambanız kapatıldı!")
        elif cmd == 'cycle':
            item = bulb.cycle_color()
            print(f"Renk değiştirildi: {item['name']}")
            send_notification(f"🎨 Renk değiştirildi: {item['name']}")
        elif cmd == 'status':
            res = bulb.get_status()
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif cmd == 'bright' and len(sys.argv) >= 3:
            val = int(sys.argv[2])
            bulb.set_brightness(val)
            print(f"Parlaklık %{val} yapıldı.")
            send_notification(f"☀️ Parlaklık %{val} yapıldı.")
        elif cmd == 'temp' and len(sys.argv) >= 3:
            val = int(sys.argv[2])
            bulb.set_color_temp(val)
            print(f"Renk sıcaklığı %{val} yapıldı.")
            send_notification(f"🌡️ Renk sıcaklığı %{val} yapıldı.")
        elif cmd == 'rgb' and len(sys.argv) >= 4:
            r, g, b = sys.argv[2], sys.argv[3], sys.argv[4]
            bulb.set_rgb(r, g, b)
            print(f"RGB Renk R:{r} G:{g} B:{b} olarak ayarlandı.")
            send_notification(f"🎨 Renk ayarlandı: RGB({r}, {g}, {b})")
        elif cmd == 'white':
            bulb.set_white()
            print("Beyaz ışık moduna geçildi.")
            send_notification("💡 Beyaz ışık moduna geçildi.")
        else:
            print_help()
    except Exception as e:
        print(f"Hata: {e}")
        send_notification(f"⚠️ Hata: {e}")

if __name__ == '__main__':
    main()
