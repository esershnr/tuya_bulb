from flask import Flask, render_template, jsonify, request
from bulb_controller import TuyaBulbController

app = Flask(__name__)
bulb = None

def get_bulb():
    global bulb
    if bulb is None:
        bulb = TuyaBulbController()
    return bulb

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/on', methods=['POST'])
def api_on():
    try:
        get_bulb().turn_on()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/off', methods=['POST'])
def api_off():
    try:
        get_bulb().turn_off()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/brightness', methods=['POST'])
def api_brightness():
    try:
        data = request.json
        val = data.get('value', 100)
        get_bulb().set_brightness(val)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/color_temp', methods=['POST'])
def api_color_temp():
    try:
        data = request.json
        val = data.get('value', 50)
        get_bulb().set_color_temp(val)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/rgb', methods=['POST'])
def api_rgb():
    try:
        data = request.json
        r, g, b = data.get('r', 255), data.get('g', 255), data.get('b', 255)
        get_bulb().set_rgb(r, g, b)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/white', methods=['POST'])
def api_white():
    try:
        get_bulb().set_white()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Tuya Web Kontrol Arayüzü Başlatılıyor...")
    print("📍 Yerel erişim: http://localhost:5000")
    print("📍 Evdeki diğer cihazlardan erişim (Tel/Tablet): http://<BILGISAYAR_IP_ADRESI>:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
