from flask import Flask, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from google.cloud import storage
from google.oauth2 import service_account
import requests, json, os
from datetime import datetime

credentials_info = {
  "type": "service_account",
  "project_id": "clear-truth-fff",
  "private_key_id": "xxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\\+/+/\/23ua5aJJPNNkaWUc7lodT9kIWxtVmJ65dPbOSFw8JGDlUZ/XUdJzev0gLOR\nXxCwLVeSVR8hIC8KOGysTyqAXe8k3wCl6MPag7rKE0MzSqvutqKBKAOO0ugQz84v\noBsjJKGdrb/1bWxlPFF212XsIehT8CsigT+t/MIgKyZiiyJzjPVMW75E6RZVGEqm\n8GkdLij+hOgjD0D2l2+L27cXU/OVdy4ycuUkm5fsK0f0v4ZlwY67KyhBSrtc8fqh\nSJJCjYe5AgMBAAECggEAEaUN5NBvdwEvLE5IDROOVc93kCf2PcEQ2mw0sS1U4Jtk\n34rr5sayWLdTf3BK570j3+cYqy5fbG0iuQpltY+lYhRQflFf9dWsFwabA4uCs3ji\nMz27XJ+uKWoNdS13f0FjfnjkR/45TXbfO3f50x03tvHosCqPRf8lh8MdaNKzreXn\no69zB8/Ian7/AUA2tVXfVXwwdVxpcaqnutB3jfHKn3m8oLbVxegJmhKdFEfLGpE8\nNyavAMZ8khZzqBP900dh43plRBAdxiob6V4V1HqR1hLi+mCj4rFEais2ZURP8hbn\nhLB2e6e3WYun8vWEt0F7vLZ/1ABImmAvWL5V3e4HRQKBgQDDyLZ1vQlDgihyCTQd\nKKLP00fh4YsETWnDeDNCVQcc/Id2gwB6q7w2QwvszkzJVqV9Q7QamW7Z+6riM+E8\nhP6x0Zx+GRfTFzHDpXtKbesL47Nf5aHFOH9WSPCBE35n+ouyp5Z95Abmv1P0FpLd\npGme0ffSpNe/zTZjZQVvHoS7rwKBgQC6pi0hrQQk+6ajRZsP6Oo/F0/HoM1xHLtJ\n94mXmWTS3X8E9AnT9vBWSvOaBD1cWOR06b0OF4JkoezCwmDGw8Ln10QT8mLiqQAG\n6WCq8ZyZDie8+Ua7cJJsQ3fBK7lRottAhkeGgIDgyiahbdFn2pYg0rmG5Jc91u/F\n2WSFML3FFwKBgAQBjmI4XQEpn6Q9tfhGxZYVD6p6j/qljt12Dy5zSPL549ez9IWO\nEArYMl1FF2MjR72Zbg0BSLhjIur//sLbQc7nqBkYcFlcZyNGtpAeUanrndb/fuDn\nOAvO8ETj3jlIciVUsoqe6Nk93vzmnVi1rYeXakfAIb4F9+/uuD6+1B53AoGAGOWt\nw342vVAsLD9OrdKd3IiZhcF3Zg01FmrEmcpGXrJZDSoYXYPlDz20POkv3i+lWcsM\nAuMz64SF9nzDOABI8XAPjrGYay+r50AeOu87ulbfCiAeRUaA4ZwmT0gr0i3tHTBM\nPi7KAjI08PebJUVNHVe+k7XOTttq5HNZK0MTLUUCgYEAgPPQV+BVYPED72413jxI\nnS58babiMsxtN00GL4FlgO3zCYU08CpfcbW/SmqrmJpYqNcUlu9xz5cIuMYfr1x8\nTgNjiTIT37qi+bBx+tQJafgQNPuClqqe5IMimf7TBBBm6s+1cw4u6USlhnmW10pi\nKtRzitfydAW4gkk3CSt5Phw=\n-----END PRIVATE KEY-----\n",
  "client_email": "adminattendance@clear-truth-416206.iam.gserviceaccount.com",
  "client_id": "hhh",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www..com/robot/v1/iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

app = Flask(__name__)
credentials = service_account.Credentials.from_service_account_info(credentials_info)
storage_client = storage.Client(credentials=credentials, project=credentials_info['project_id'])
bucket_name = 'attendance_management_system'
bucket = storage_client.bucket(bucket_name)

DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')
@app.route('/submit', methods=['POST'])
def submit():
    if 'photo' not in request.files or 'rollNo' not in request.form:
        return jsonify({'error': 'Missing photo or roll number'}), 400
    
    photo = request.files['photo']
    name = request.form['name']
    roll_no = request.form['rollNo']
    image_url = upload_image_to_gcs(photo, roll_no)
    if image_url is None:
        return jsonify({'error': 'Failed to upload image'}), 500
    
    emotion_data = detect_emotion(image_url)
    if emotion_data != 'Error':
        save_attendance_record(roll_no, name, image_url, emotion_data['emotion'], emotion_data['accuracy'])
        return jsonify({'message': 'Submission successful', 'rollNo': roll_no, **emotion_data}), 200
    else:
        return jsonify({'error': 'Emotion detection failed'}), 500

def upload_image_to_gcs(file_stream, roll_no):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{secure_filename(roll_no)}_{timestamp}.jpg"
    blob = bucket.blob(filename)
    try:
        blob.upload_from_string(file_stream.read(), content_type=file_stream.content_type)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None

def save_attendance_record(roll_no, name, image_url, emotion, accuracy):
    filepath = os.path.join(DATA_DIR, f'{roll_no}.json')
    record = {'rollNo': roll_no, 'name': name, 'image_url': image_url, 'emotion': emotion, 'accuracy': accuracy, 'date': datetime.now().strftime('%Y-%m-%d')}
    if not os.path.exists(filepath):
        with open(filepath, 'w') as file:
            json.dump([record], file, indent=4)
    else:
        with open(filepath, 'r+') as file:
            records = json.load(file)
            records.append(record)
            file.seek(0)
            json.dump(records, file, indent=4)
            file.truncate()

def detect_emotion(image_url):
    try:
        url = "https://emotion-detection2.p.rapidapi.com/emotion-detection"
        payload = {"url": image_url}
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": "xxxc",
            "X-RapidAPI-Host": "emotion-detection2.p.rapidapi.com"
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            emotions = response.json()
            if emotions:
                primary_emotion = emotions[0]['emotion']['value']
                probability = emotions[0]['emotion']['probability'] * 100
                return {'emotion': primary_emotion, 'accuracy': f"{probability:.2f}%"}
        return 'Error'
    except Exception as e:
        print(f"Exception calling emotion API: {e}")
        return 'Error'

import csv
import json
import os

def generate_csv(filepath):
    with open(filepath, 'r') as json_file:
        records = json.load(json_file)

    # Define a path for the CSV file
    csv_file_path = filepath.replace('.json', '.csv')

    # Define CSV columns
    columns = ['rollNo', 'name', 'image_url', 'emotion', 'accuracy', 'date']

    # Write the JSON data to a CSV file
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()
        for record in records:
            writer.writerow(record)

    return csv_file_path

@app.route('/download-report/<roll_no>', methods=['GET'])
def download_report(roll_no):
    filepath = os.path.join(DATA_DIR, f'{roll_no}.json')
    if os.path.exists(filepath):
        csv_file_path = generate_csv(filepath)
        return send_file(csv_file_path, as_attachment=True, download_name=f'{roll_no}_report.csv')
    else:
        return jsonify({'error': 'Report not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
