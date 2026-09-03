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
Kullanım: python main.py <komut> [parametreler]...

Birden fazla komut peş peşe verilebilir (Örn: python main.py toggle bright 50 temp 35)

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
    args = sys.argv[1:] if len(sys.argv) > 1 else ['toggle']

    if any(a.lower() in ['-h', '--help', 'help'] for a in args):
        print_help()
        return

    # --- 1. ARGÜMANLARI AYRIŞTIRMA VE DOĞRULAMA (VALIDATION) ---
    actions = []
    bright_val = None
    temp_val = None
    rgb_val = None
    has_white = False

    i = 0
    while i < len(args):
        cmd = args[i].lower()

        if cmd in ['on', 'off', 'toggle', 'cycle', 'status']:
            actions.append(cmd)
            i += 1
        elif cmd == 'white':
            has_white = True
            i += 1
        elif cmd == 'bright':
            if i + 1 >= len(args):
                print("Hata: 'bright' için 1-100 arasında bir değer belirtilmelidir.")
                return
            try:
                val = int(args[i + 1])
                if not (1 <= val <= 100):
                    print(f"Hata: Parlaklık (bright) 1 ile 100 arasında olmalıdır (Girilen: {val}).")
                    return
                bright_val = val
            except ValueError:
                print(f"Hata: 'bright' parametresi sayı olmalıdır (Girilen: {args[i + 1]}).")
                return
            i += 2
        elif cmd == 'temp':
            if i + 1 >= len(args):
                print("Hata: 'temp' için 0-100 arasında bir değer belirtilmelidir.")
                return
            try:
                val = int(args[i + 1])
                if not (0 <= val <= 100):
                    print(f"Hata: Renk sıcaklığı (temp) 0 ile 100 arasında olmalıdır (Girilen: {val}).")
                    return
                temp_val = val
            except ValueError:
                print(f"Hata: 'temp' parametresi sayı olmalıdır (Girilen: {args[i + 1]}).")
                return
            i += 2
        elif cmd == 'rgb':
            if i + 3 >= len(args):
                print("Hata: 'rgb' için 3 değer belirtilmelidir (r g b). Örn: rgb 255 0 0")
                return
            try:
                r, g, b = int(args[i + 1]), int(args[i + 2]), int(args[i + 3])
                for name, c in [('R', r), ('G', g), ('B', b)]:
                    if not (0 <= c <= 255):
                        print(f"Hata: RGB {name} değeri 0-255 arasında olmalıdır (Girilen: {c}).")
                        return
                rgb_val = (r, g, b)
            except ValueError:
                print("Hata: 'rgb' parametreleri 0-255 arasında tam sayı olmalıdır.")
                return
            i += 4
        else:
            print(f"Bilinmeyen komut veya geçersiz parametre: {cmd}")
            print_help()
            return

    # Mantıksal Çelişki Kontrolleri:
    # RGB modundayken 'temp' (renk sıcaklığı) fiziksel olarak yoktur.
    if rgb_val is not None and temp_val is not None:
        print("Hata: 'rgb' ve 'temp' aynı anda kullanılamaz! Renk sıcaklığı (temp) yalnızca beyaz ışık modunda geçerlidir.")
        return

    # RGB ve Beyaz mod seçimi çelişkisi
    if rgb_val is not None and has_white:
        print("Hata: Hem 'rgb' hem 'white' aynı anda belirtilemez.")
        return

    # --- 2. AMPUL İŞLEMLERİNİ YÜRÜTME ---
    try:
        bulb = TuyaBulbController()
    except Exception as e:
        print(f"Hata: {e}")
        send_notification(f"⚠️ Hata: {e}")
        return

    notifications = []

    try:
        # Önce temel eylemleri işlet (on, off, toggle, cycle, status)
        for act in actions:
            if act == 'on':
                bulb.turn_on()
                print("Ampul AÇILDI")
                notifications.append("💡 Ampul Açıldı")
            elif act == 'off':
                bulb.turn_off()
                print("Ampul KAPATILDI")
                notifications.append("🌑 Ampul Kapatıldı")
                if bright_val or temp_val or rgb_val or has_white:
                    print("Ampul kapatıldığı için renk/parlaklık ayarları uygulanmadı.")
                send_notification("🌑 Ampul Kapatıldı")
                return
            elif act == 'toggle':
                is_now_on = bulb.toggle()
                if is_now_on:
                    print("Ampul AÇILDI")
                    notifications.append("💡 Ampul Açıldı")
                else:
                    print("Ampul KAPATILDI")
                    notifications.append("🌑 Ampul Kapatıldı")
                    if bright_val or temp_val or rgb_val or has_white:
                        print("Ampul kapatıldığı için renk/parlaklık ayarları uygulanmadı.")
                    send_notification("🌑 Ampul Kapatıldı")
                    return
            elif act == 'cycle':
                item = bulb.cycle_color()
                print(f"Renk değiştirildi: {item['name']}")
                notifications.append(f"🎨 Renk: {item['name']}")
            elif act == 'status':
                res = bulb.get_status()
                print(json.dumps(res, indent=2, ensure_ascii=False))

        # Renk ve Parlaklık Modları
        if rgb_val:
            r, g, b = rgb_val
            bulb.set_rgb(r, g, b)
            print(f"RGB Renk R:{r} G:{g} B:{b} olarak ayarlandı.")
            notifications.append(f"🎨 RGB({r}, {g}, {b})")
        elif bright_val is not None and temp_val is not None:
            # Hem parlaklık hem sıcaklık varsa tek paket ile atomic gönder
            bulb.set_white(brightness=bright_val, color_temp=temp_val)
            print(f"Beyaz Işık ayarlandı: Parlaklık %{bright_val}, Sıcaklık %{temp_val}")
            notifications.append(f"☀️ Parlaklık %{bright_val} | 🌡️ Sıcaklık %{temp_val}")
        elif bright_val is not None:
            bulb.set_brightness(bright_val)
            print(f"Parlaklık %{bright_val} yapıldı.")
            notifications.append(f"☀️ Parlaklık %{bright_val}")
        elif temp_val is not None:
            bulb.set_color_temp(temp_val)
            print(f"Renk sıcaklığı %{temp_val} yapıldı.")
            notifications.append(f"🌡️ Sıcaklık %{temp_val}")
        elif has_white:
            bulb.set_white()
            print("Beyaz ışık moduna geçildi.")
            notifications.append("💡 Beyaz Mod")

        if notifications:
            send_notification(" | ".join(notifications))

    except Exception as e:
        print(f"Hata: {e}")
        send_notification(f"⚠️ Hata: {e}")

if __name__ == '__main__':
    main()
