# Tuya Akıllı Ampul Kontrolü

Dotfiles altında Windows kısayolları ve otomasyonlar için Tuya akıllı ampul kontrol altyapısı.

---

## ⚡ Aktif: Yerel (LAN) Kontrol

İç ağ üzerinden doğrudan ampulün IP'sine şifreli paketler gönderir.

- **API limiti yok**, **gecikme minimum**.
- **`tinytuya` + `local_key`** altyapısıyla çalışır.
- İnternet bağlantısı kesilse bile yerel WiFi üzerinden tam kontrol sağlar.

### 🛠️ Kurulum ve Hazırlık

1. Gerekli kütüphaneleri yükleyin:

   ```bash
   pip install -r requirements.txt
   ```

   _(Gereksinimler: `tinytuya`, `flask`, `windows_toasts`, `python-dotenv`)_

2. **Local Key ve Device ID Alma (Bir Kereliğine):**
   Tuya cihazlarında yerel şifreleme olduğu için `local_key` bilgisine ihtiyaç vardır.
   - **Otomatik (Önerilen):** `python -m tinytuya wizard` çalıştırarak ağdaki cihazları tarayıp `devices.json` oluşturabilirsiniz.
   - **Tuya Developer Platform:** Cloud Console -> Cloud Services -> API Explorer üzerinden cihaz detaylarından `local_key` değerini alabilirsiniz.

3. **Konfigürasyon (`.env` veya `config.json`):**
   `.env.example` dosyasını `.env` olarak (veya `config.example.json` dosyasını `config.json` olarak) kopyalayıp bilgilerinizi girin:
   ```env
   TUYA_DEVICE_ID="[DEVICE_ID]"
   TUYA_IP="[BULB_IP_ADDRESS]"
   TUYA_LOCAL_KEY="[LOCAL_KEY]"
   TUYA_VERSION=3.3
   ```

### 🚀 Kullanım Yöntemleri

#### 1. Komut Satırı (CLI) ve Kısayollar

`main.py` komutları Windows 10/11 Bildirim Merkezi (Toast) entegrasyonuna sahiptir:

```bash
# Ampulü aç / kapat
python main.py on
python main.py off

# Durumu tersine çevir (Toggle)
python main.py toggle

# Renk döngüsü (RGB Cycle)
python main.py cycle

# Parlaklık ayarla (1 - 100)
python main.py bright 75

# Renk sıcaklığı ayarla (0=Sıcak, 100=Soğuk)
python main.py temp 50

# Özel RGB rengi
python main.py rgb 255 0 0

# Beyaz ışık modu
python main.py white

# Durum bilgisi
python main.py status
```

#### 2. Cihaz Taraması & Otomatik IP Güncelleme (`discover.py`)

Modem yeniden başladığında veya ampulün IP'si değiştiğinde:

```bash
# Etkileşimli tarama
python discover.py

# Doğrudan bulunan IP ile .env dosyasını güncelle
python discover.py --update
```

#### 3. Web Arayüzü (`app.py`)

Telefon, tablet veya bilgisayardan yerel arayüz:

```bash
python app.py
```

- Tarayıcı: `http://localhost:5000` veya yerel ağdaki `http://<BILGISAYAR_IP>:5000`

---

## 📦 legacy/ — Bulut (Tuya Cloud API) Sürümü

İlk deneme sürümüdür. Tuya IoT projesine `apiKey` / `apiSecret` ile bağlanıp cloud API üzerinden kontrol ediyordu (`tuya-connector-python`).

### Neden Terk Edildi?

- **İnternet Bağımlılığı:** Her komut Tuya bulut sunucularına gidip geldiği için gecikme (latency) yüksekti.
- **Rate Limit:** Tuya Cloud API istek limitleri mevcuttu ve kota dolumunda çalışmıyordu.
- **Offline Durum:** İnternet kesintisinde cihaz lokalde olsa dahi kontrol edilemiyordu.

### Neden Hâlâ Saklanıyor?

- `local_key` çekip yerel sürüme geçmek ve cihaz eşleştirmesini ilk kez kurmak için Tuya Cloud kimlik bilgileri hâlâ işe yarar (`tinytuya wizard`).

---

## 🔒 Gizlilik & Güvenlik

- Gizli anahtarlar (`local_key`, `apiKey`, `apiSecret`, `.env`, `config.json`, `devices.json`) `.gitignore` ile korunmaktadır.
- Yerel LAN sürümü bilgisayarınızdan Tuya bulutuna herhangi bir veri göndermez; tüm paketler yerel ağda şifreli TCP ile aktarılır.
