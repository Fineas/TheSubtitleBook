from scanner import Servo
from flask import Flask, request, render_template, send_from_directory
import requests
import os
import hashlib
import time
from PIL import Image

app = Flask(__name__)

SCAN_FOLDER = os.path.join('static', 'scans')
if not os.path.exists(SCAN_FOLDER):
    os.makedirs(SCAN_FOLDER)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/scan_book', methods=['GET'])
def scan_book():
    servo = Servo()  # instance of the Servo class

    pages = int(request.args.get('pages', 1)) 

    # random folder name
    folder_name = hashlib.sha256(os.urandom(8)).hexdigest()[:8]
    folder_path = os.path.join(SCAN_FOLDER, folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # press on the page
    servo.get_down()
    time.sleep(1) 

    # loop through the pages
    for i in range(pages):
        print(f"[*] Scanning Pages {i*2-1} - {i*2}")
        response = requests.get('http://192.168.134.70:8080/capture')

        image_path = os.path.join(folder_path, f'{i}.png')
        with open(image_path, 'wb') as f:
            f.write(response.content)
            print(" > success \n")
        
        image = Image.open(image_path)
        width, height = image.size

        # split the image
        left_half = image.crop((0, 0, width // 2, height))
        right_half = image.crop((width // 2, 0, width, height))

        if i == 0:
            # the first scan is just the cover so only save right side
            right_half.save(os.path.join(folder_path, 'cover.jpg'))
            os.remove(image_path)  # delete the original full image
        else:
            left_half.save(os.path.join(folder_path, f'{i*2-1}.jpg'))
            right_half.save(os.path.join(folder_path, f'{i*2}.jpg'))
            os.remove(image_path)  # delete the original full image

        # get back up and turn the page
        servo.get_up()
        time.sleep(1)

        if i < pages-1:
            servo.turn_page()
            print("[*] next \n")
        # time.sleep(1)  # wait...

    return {"status": "Scanning complete", "folder": folder_name}

@app.route('/scans/<scan_path>')
def dir_listing(scan_path):

    abs_path = os.path.join(SCAN_FOLDER, scan_path)

    if not os.path.exists(abs_path):
        return abort(404)

    # if os.path.isfile(abs_path):
    #     return send_file(abs_path)

    # dir list
    files = os.listdir(abs_path)
    return render_template('dir_listing.html', files=files)

if __name__ == '__main__':
    app.run(host='192.168.134.198', port=1337)
