import json
import os
import colorsys
import tinytuya
from config import load_config

STATE_FILE = os.path.join(os.path.dirname(__file__), '.state.json')

CYCLE_COLORS = [
    {"type": "rgb", "value": (255, 0, 0), "name": "Kırmızı"},
    {"type": "rgb", "value": (0, 255, 0), "name": "Yeşil"},
    {"type": "rgb", "value": (0, 0, 255), "name": "Mavi"},
    {"type": "rgb", "value": (255, 255, 0), "name": "Sarı"},
    {"type": "rgb", "value": (0, 255, 255), "name": "Turkuaz"},
    {"type": "rgb", "value": (255, 0, 255), "name": "Mor"},
    {"type": "rgb", "value": (255, 128, 0), "name": "Turuncu"}
]

class TuyaBulbController:
    def __init__(self, device_id=None, ip=None, local_key=None, version=None):
        config = load_config()
        self.device_id = device_id or config.get('device_id')
        self.ip = ip or config.get('ip', 'AUTO')
        self.local_key = local_key or config.get('local_key')
        self.version = float(version if version is not None else config.get('version', 3.3))
        
        self.device = tinytuya.BulbDevice(
            dev_id=self.device_id,
            address=self.ip if self.ip != 'AUTO' else None,
            local_key=self.local_key,
            version=self.version
        )
        self.device.set_socketRetryLimit(1)
        self.device.set_socketTimeout(2)

    def _check_response(self, res):
        """Tinytuya yanıtını denetler, hata varsa ConnectionError fırlatır."""
        if not isinstance(res, dict):
            raise ConnectionError(f"Cihazdan beklenmeyen yanıt: {res}")
        if 'Error' in res or 'Err' in res:
            err_msg = res.get('Error', f"Hata Kodu: {res.get('Err')}")
            raise ConnectionError(f"Ampule bağlanılamadı (IP: {self.ip}): {err_msg}")
        return res

    def turn_on(self):
        """Ampulü açar (DP 20 = True)."""
        res = self.device.set_status(True, 20)
        return self._check_response(res)

    def turn_off(self):
        """Ampulü kapatır (DP 20 = False)."""
        res = self.device.set_status(False, 20)
        return self._check_response(res)

    def toggle(self):
        """Durumu tersine çevirir. Kapalıysa Sıcak Beyaz (%50 parlaklık, %35 sıcaklık) ile açar. Yeni durumu (True=Açık, False=Kapalı) döner."""
        status = self.get_status()
        dps = status.get('dps', {})
        is_on = dps.get('20', dps.get('1', False))
        if is_on:
            self.turn_off()
            return False
        else:
            self.set_white(brightness=50, color_temp=35)
            return True

    def set_brightness(self, percent):
        """Beyaz ışık parlaklığını 1 - 100 arasında ayarlar (DP 22: 10 - 1000)."""
        percent = max(1, min(100, int(percent)))
        val = int(percent * 10)  # 1-100 -> 10-1000
        payload = {
            '20': True,
            '21': 'white',
            '22': val
        }
        res = self.device.set_multiple_values(payload)
        return self._check_response(res)

    def set_color_temp(self, percent):
        """Renk sıcaklığını (Sıcak/Soğuk beyaz) 0 - 100 arasında ayarlar (DP 23: 0 - 1000)."""
        percent = max(0, min(100, int(percent)))
        val = int(percent * 10)  # 0-100 -> 0-1000
        payload = {
            '20': True,
            '21': 'white',
            '23': val
        }
        res = self.device.set_multiple_values(payload)
        return self._check_response(res)

    def set_rgb(self, r, g, b):
        """RGB renge geçer (DP 21: 'colour', DP 24: HHHHSSSSVVVV)."""
        r, g, b = int(r), int(g), int(b)
        r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
        h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
        
        h_deg = int(h * 360)
        s_val = int(s * 1000)
        v_val = int(v * 1000)
        
        # En azından görünür parlaklık olsun
        if v_val < 100 and (r > 0 or g > 0 or b > 0):
            v_val = 1000

        hex_str = f"{h_deg:04x}{s_val:04x}{v_val:04x}"
        
        payload = {
            '20': True,
            '21': 'colour',
            '24': hex_str
        }
        res = self.device.set_multiple_values(payload)
        return self._check_response(res)

    def set_white(self, brightness=100, color_temp=50):
        """Beyaz ışık moduna geçer."""
        bright_val = int(max(1, min(100, brightness)) * 10)
        temp_val = int(max(0, min(100, color_temp)) * 10)
        payload = {
            '20': True,
            '21': 'white',
            '22': bright_val,
            '23': temp_val
        }
        res = self.device.set_multiple_values(payload)
        return self._check_response(res)

    def cycle_color(self):
        """Renkler arasında sırayla (RGB cycle) geçiş yapar."""
        current_index = -1
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    current_index = state_data.get('color_index', -1)
            except Exception:
                current_index = -1

        next_index = (current_index + 1) % len(CYCLE_COLORS)

        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump({'color_index': next_index}, f)
        except Exception as e:
            print(f"Durum dosyası kaydedilemedi: {e}")

        color_item = CYCLE_COLORS[next_index]
        if color_item['type'] == 'rgb':
            r, g, b = color_item['value']
            self.set_rgb(r, g, b)
        elif color_item['type'] == 'white':
            b_val = color_item.get('brightness', 100)
            c_temp = color_item.get('color_temp', 0)
            self.set_white(brightness=b_val, color_temp=c_temp)

        return color_item

    def get_status(self):
        """Cihazın anlık durumunu döndürür."""
        res = self.device.status()
        self._check_response(res)
        if 'dps' not in res:
            raise ConnectionError(f"Cihaz durum bilgisi (dps) alınamadı (IP: {self.ip}).")
        return res


if __name__ == '__main__':
    # Hızlı test
    try:
        bulb = TuyaBulbController()
        print("Cihaz durumu alınıyor...")
        print(json.dumps(bulb.get_status(), indent=2))
    except Exception as e:
        print(f"Hata: {e}")
