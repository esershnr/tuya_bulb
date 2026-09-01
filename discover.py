import os
import sys
import json
import socket
import concurrent.futures
import tinytuya
from config import load_config, update_config_ip

def get_local_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '192.168.1.1'
    finally:
        s.close()
    
    parts = local_ip.split('.')
    subnet = '.'.join(parts[:3])
    return local_ip, subnet

def check_tuya_port(ip):
    """Tuya yerel kontrol portunu (TCP 6668) kontrol eder."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.35)
    try:
        if sock.connect_ex((ip, 6668)) == 0:
            return ip
    except Exception:
        pass
    finally:
        sock.close()
    return None

def scan_network():
    local_ip, subnet = get_local_subnet()
    print(f"[*] Ag taraniyor (Yerel IP: {local_ip}, Alt Ag: {subnet}.0/24)...")
    
    # Hızlı alt ağ TCP 6668 port taraması (Multithreaded)
    active_tuya_ips = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        target_ips = [f"{subnet}.{i}" for i in range(1, 255)]
        results = executor.map(check_tuya_port, target_ips)
        for res in results:
            if res:
                active_tuya_ips.append(res)
    
    config = load_config()
    cfg_dev_id = config.get('device_id')
    cfg_key = config.get('local_key')
    cfg_version = float(config.get('version', 3.3))
    cfg_ip = config.get('ip')

    found_devices = []

    for ip in active_tuya_ips:
        dev_info = {
            'ip': ip,
            'id': 'Bilinmiyor',
            'version': str(cfg_version),
            'status': 'Cevrimici',
            'matched': False
        }
        
        # Eğer config'de key varsa sorgula ve doğrula
        if cfg_dev_id and cfg_key:
            try:
                test_dev = tinytuya.BulbDevice(dev_id=cfg_dev_id, address=ip, local_key=cfg_key, version=cfg_version)
                test_dev.set_socketTimeout(1.0)
                test_dev.set_socketRetryLimit(1)
                st = test_dev.status()
                if isinstance(st, dict) and 'dps' in st:
                    dev_info['id'] = cfg_dev_id
                    dev_info['matched'] = True
                    dev_info['status'] = 'Eslesme Dogrulandi'
            except Exception:
                pass
        
        found_devices.append(dev_info)

    if not found_devices:
        print("\n[-] Yerel agda acik Tuya cihazi (Port 6668) bulunamadi.")
        print("Lutfen bilgisayarinizin ve ampulun ayni WiFi agina bagli oldugundan ve ampulun acik oldugundan emin olun.")
        return

    print(f"\n[+] {len(found_devices)} adet Tuya cihazi tespit edildi:\n")
    print("=" * 70)
    print(f"{'IP Adresi':<18} | {'Device ID':<26} | {'Durum'}")
    print("=" * 70)
    
    matched_ip = None
    for dev in found_devices:
        print(f"{dev['ip']:<18} | {dev['id']:<26} | {dev['status']}")
        if dev['matched'] or dev['id'] == cfg_dev_id:
            matched_ip = dev['ip']

    print("=" * 70)

    if matched_ip:
        print(f"\n[!] Yapılandırmadaki Device ID ({cfg_dev_id}) için aktif IP: {matched_ip}")
        if cfg_ip != matched_ip:
            print(f"[!] Mevcut IP ({cfg_ip}) GEÇERSİZ / ESKİ!")
            if '--update' in sys.argv or '-u' in sys.argv:
                update_config_ip(matched_ip)
            else:
                try:
                    choice = input(f"\n.env dosyasını doğru IP ({matched_ip}) ile güncellemek ister misiniz? (E/h): ").strip().lower()
                    if choice in ['e', 'evet', 'y', 'yes', '']:
                        update_config_ip(matched_ip)
                except (EOFError, KeyboardInterrupt):
                    pass
        else:
            print("[+] Yapılandırmadaki IP adresi zaten doğru ve aktif.")
    else:
        print("\nİpucu: Tespit edilen IP adresini .env dosyasına yazabilirsiniz.")

if __name__ == '__main__':
    scan_network()
