import os
import sys
import json
import re

# Windows konsolunda UTF-8 karakterlerin sorunsuz yazılmasını sağla
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
TINYTUYA_FILE = os.path.join(os.path.dirname(__file__), 'tinytuya.json')

def _parse_env_line(line):
    """Basit bir .env satırını ayrıştırır (anahtar=değer)."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None
    if '=' not in line:
        return None, None
    key, val = line.split('=', 1)
    key = key.strip()
    val = val.strip()
    # Tırnak işaretlerini kaldır (tek veya çift tırnak)
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]
    return key, val

def load_env_file():
    """dotenv kütüphanesi varsa onu kullanır, yoksa yerleşik basit parser ile .env yükler."""
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=ENV_FILE, override=False)
    except ImportError:
        # python-dotenv yüklü değilse dahili fallback parser
        if os.path.exists(ENV_FILE):
            try:
                with open(ENV_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        k, v = _parse_env_line(line)
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception as e:
                print(f"Uyarı: .env dosyası okunurken hata oluştu: {e}")

def load_config():
    """
    Öncelikle .env ve ortam değişkenlerinden, bulunamazsa config.json ve tinytuya.json 
    dosyalarından cihaz ve API yapılandırmasını yükler.
    """
    load_env_file()

    # Ortam değişkenlerinden oku
    device_id = os.environ.get('TUYA_DEVICE_ID') or os.environ.get('DEVICE_ID')
    ip = os.environ.get('TUYA_IP') or os.environ.get('IP')
    local_key = os.environ.get('TUYA_LOCAL_KEY') or os.environ.get('LOCAL_KEY')
    version_str = os.environ.get('TUYA_VERSION') or os.environ.get('VERSION')
    api_key = os.environ.get('TUYA_API_KEY') or os.environ.get('API_KEY')
    api_secret = os.environ.get('TUYA_API_SECRET') or os.environ.get('API_SECRET')
    api_region = os.environ.get('TUYA_API_REGION') or os.environ.get('API_REGION', 'eu')

    # Geriye dönük uyumluluk: config.json fallback
    json_cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                json_cfg = json.load(f)
        except Exception:
            json_cfg = {}

    # tinytuya.json fallback (Cloud API için)
    tinytuya_cfg = {}
    if os.path.exists(TINYTUYA_FILE):
        try:
            with open(TINYTUYA_FILE, 'r', encoding='utf-8') as f:
                tinytuya_cfg = json.load(f)
        except Exception:
            tinytuya_cfg = {}

    device_id = device_id or json_cfg.get('device_id') or tinytuya_cfg.get('apiDeviceID')
    ip = ip or json_cfg.get('ip', 'AUTO')
    local_key = local_key or json_cfg.get('local_key')
    
    if version_str:
        try:
            version = float(version_str)
        except ValueError:
            version = 3.3
    else:
        version = float(json_cfg.get('version', 3.3))

    api_key = api_key or tinytuya_cfg.get('apiKey')
    api_secret = api_secret or tinytuya_cfg.get('apiSecret')
    api_region = api_region or tinytuya_cfg.get('apiRegion', 'eu')

    if not device_id or not local_key:
        raise ValueError(
            "Cihaz yapılandırması eksik! Lütfen .env dosyasında TUYA_DEVICE_ID ve TUYA_LOCAL_KEY tanımlayın "
            "(veya .env.example dosyasını .env olarak kopyalayıp doldurun)."
        )

    return {
        'device_id': str(device_id),
        'ip': str(ip),
        'local_key': str(local_key),
        'version': version,
        'api_key': str(api_key) if api_key else None,
        'api_secret': str(api_secret) if api_secret else None,
        'api_region': str(api_region) if api_region else 'eu'
    }

def update_config_ip(new_ip):
    """
    Tespit edilen yeni IP adresini .env dosyasına (ve varsa config.json dosyasına) kaydeder.
    """
    os.environ['TUYA_IP'] = str(new_ip)
    
    # 1. .env dosyasını güncelle veya oluştur
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated = False
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('TUYA_IP=') or stripped.startswith('IP='):
                prefix = 'TUYA_IP=' if stripped.startswith('TUYA_IP=') else 'IP='
                new_lines.append(f"{prefix}{new_ip}\n")
                updated = True
            else:
                new_lines.append(line)
        
        if not updated:
            new_lines.append(f"\nTUYA_IP={new_ip}\n")
        
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    else:
        # .env dosyası henüz yoksa oluştur
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write(f"TUYA_IP={new_ip}\n")

    # 2. Varsa config.json dosyasını da güncelle
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            cfg['ip'] = new_ip
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    print(f"\n[+] IP adresi ({new_ip}) .env dosyasında başarıyla güncellendi!")

def mask_secret(val):
    """Hassas anahtarların ekranda güvenli gösterimi için maskeleme."""
    if not val:
        return "<yok>"
    if len(val) <= 6:
        return "***"
    return f"{val[:3]}...{val[-3:]}"

if __name__ == '__main__':
    try:
        cfg = load_config()
        print("=== Tuya Yapılandırma Bilgileri ===")
        print(f"Device ID   : {cfg['device_id']}")
        print(f"IP Adresi   : {cfg['ip']}")
        print(f"Local Key   : {mask_secret(cfg['local_key'])}")
        print(f"Sürüm       : {cfg['version']}")
        print(f"API Key     : {mask_secret(cfg['api_key'])}")
        print(f"API Secret  : {mask_secret(cfg['api_secret'])}")
        print(f"API Region  : {cfg['api_region']}")
        print("===================================")
        print("✅ Yapılandırma başarıyla doğrulandı.")
    except Exception as e:
        print(f"❌ Yapılandırma Hatası: {e}")
