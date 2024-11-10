import os
import sys
import json
import ollama
import hashlib
import requests
import threading
from flask_cors import CORS
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, jsonify, redirect
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import local packages
from ocr.image2text import do_ocr, extract_json_from_text, extract_title_and_author_from_image, extract_title_and_author_from_text
from t2s.text2speech import generate_audio
from s2v.static2video import create_slideshow_with_audio


app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'static/books'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit for uploads

cert_path = os.path.join('static', 'certs', 'cert.pem')
key_path = os.path.join('static', 'certs', 'key.pem')

# global to track scan status
scan_complete = False

@app.after_request
def add_cors_headers(response):
    print("this is executing??")
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

def count_lines_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return len(file.readlines())  # count them lines
    except FileNotFoundError:
        return 0 

def fetch_image_from_prompt(prompt):
    formatted_prompt = prompt.replace("\n", "").replace(" ", "-")
    formatted_prompt += "-mid20th-century-disney-style"
    
    url = f"https://image.pollinations.ai/prompt/{formatted_prompt}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content  
        else:
            return f"Error: Received status code {response.status_code}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def split_text_into_parts(text, num_parts):
    length = len(text)
    part_size = length // num_parts
    parts = [text[i*part_size:(i+1)*part_size] for i in range(num_parts - 1)]
    parts.append(text[(num_parts - 1)*part_size:])  
    return parts

def generate_images_from_text_files(folder_path):
    # books_folder = app.config['UPLOAD_FOLDER']
    text_folder = os.path.join(folder_path, "text")
    video_folder = os.path.join(folder_path, "video")

    image_counter = 1

    print('>>',text_folder)

    for file_name in sorted(os.listdir(text_folder)):
        print(file_name)
        if file_name.endswith(".txt"):
            file_path = os.path.join(text_folder, file_name)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            parts = split_text_into_parts(text, 3)
            print(parts)

            # Pass each part to the image generation function
            for part in parts:
                image_data = fetch_image_from_prompt(part)
                
                if image_data:
                    image_path = os.path.join(video_folder, f"{image_counter}.jpg")
                    with open(image_path, 'wb') as image_file:
                        image_file.write(image_data)
                    
                    print(f"[*] Saved image {image_counter}.jpg")
                    image_counter += 1

def load_books():
    books = []
    books_folder = app.config['UPLOAD_FOLDER']
    for book_dir in os.listdir(books_folder):
        print(f"> Book: {book_dir}")
        info_path = os.path.join(books_folder, book_dir, 'info.json')
        if os.path.exists(info_path):
            with open(info_path, 'r') as file:
                book_info = json.load(file)
                books.append(book_info)
    return books

@app.route('/')
def home():
    books = load_books()
    return render_template('home.html', books=books)

@app.route('/<hash>')
def view_scans(hash):
    books_folder = app.config['UPLOAD_FOLDER']
    book_path = os.path.join(books_folder, hash, 'info.json')

    if os.path.exists(book_path):
        with open(book_path, 'r') as file:
            book_info = json.load(file)
        
        book_path = os.path.join(books_folder, hash, 'text')
        line_counts = {}
        for page in os.listdir(book_path):
            if page.endswith('.txt'):
                file_path = os.path.join(book_path, page)
                line_counts[page] = count_lines_in_file(file_path)
        return render_template('book.html', book=book_info, line_counts=line_counts)
    else:
        return "Book not found", 404

def combine_text_files(text_folder):
    combined_text = ""
    for filename in sorted(os.listdir(text_folder)):
        if filename.endswith(".txt"):
            file_path = os.path.join(text_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                combined_text += file.read() + "\n" 
    return combined_text

@app.route('/chat', methods=['POST'])
def chat_with_ollama():
    data = request.get_json()
    question = data.get('question', '')
    path = 'static/books/'+data.get('path', '')

    try:
        info_path = os.path.join(path, 'info.json')
        if not os.path.exists(info_path):
            return jsonify({'error': 'info.json not found'}), 404

        with open(info_path, 'r', encoding='utf-8') as file:
            book_info = json.load(file)

        system_prompt = "You are a book reader. You will chat with the user and answer all their questions based on the information from the following book:\n"
        system_prompt += f"Title: {book_info.get('Title', 'Unknown Title')}\n"
        system_prompt += f"Author: {book_info.get('Author', 'Unknown Author')}\n\n"
        system_prompt += combine_text_files(os.path.join(path, 'text'))

        response = ollama.chat(
            model="llama3.1:latest",
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt  
                },
                {
                    'role': 'user',
                    'content': question,
                }
            ]
        )

        content = response.get('message', {}).get('content', 'No response')
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_summary(text):
    response = ollama.chat(
        model="llama3.1:latest",
        messages=[
            {
                'role': 'system',
                'content': 'You are a summarizer. You will summarize the following text:',
            },
            {
                'role': 'user',
                'content': text,
            }
        ]
    )

    content = response.get('message', {}).get('content', 'No response')
    return content

def extract_data(local_dir):
    info_path = os.path.join(local_dir, 'info.json')
    
    with open(info_path, 'r') as f:
        info = json.load(f)

    cover_image_path = os.path.join(local_dir, 'scans', 'cover.jpg')

    # ocr the cover to extract author and title
    if os.path.exists(cover_image_path):
        print(f"[*] Performing OCR on {cover_image_path}")
        tit_auth  = json.loads(extract_json_from_text(extract_title_and_author_from_image(cover_image_path)))
        # ocr_res = do_ocr(cover_image_path)
        print("[*] Cover Result:", tit_auth)
        # title, author = extract_title_and_author_from_text(ocr_res)

        # title = ""
        # author = ""
        info["Title"] = tit_auth["title"]
        info["Author"] = tit_auth["author"]

        # print(f"[*] Title: {tit_auth["title"]}")
        # print(f"[*] Author: {tit_auth["author"]}")
    else:
        print(f"Error: Cover image {cover_image_path} not found")


    # ocr the text pages
    full_book = ''
    scans_folder = os.path.join(local_dir, 'scans')
    text_folder = os.path.join(local_dir, 'text')

    for file_name in sorted(os.listdir(scans_folder)):
        if file_name.endswith('.jpg') and file_name != 'cover.jpg':
            image_path = os.path.join(scans_folder, file_name)
            text_output_path = os.path.join(text_folder, f"{file_name.split('.')[0]}.txt")

            print(f"[*] Performing OCR on {image_path}")
            # page_text = extract_text_from_image(image_path)
            page_text = do_ocr(image_path)
            full_book += page_text

            with open(text_output_path, 'w') as text_file:
                text_file.write(page_text)
            print(f"[*] Saved OCR text to {text_output_path}")
    
    if page_text:
        info["Description"] = generate_summary(full_book)
    
    with open(info_path, 'w') as f:
        json.dump(info, f, indent=4)

def generate_video(local_dir):
    video_folder = os.path.join(local_dir, 'video')

    images = []

    for file_name in sorted(os.listdir(video_folder)):
        if file_name.endswith('.jpg'):
            images.append(os.path.join(video_folder, file_name))

    audio_path = os.path.join(local_dir, 'audio', 'output.mp3')
    duration_per_image = 25 

    create_slideshow_with_audio(images, audio_path, os.path.join(local_dir, 'video', 'movie.mp4'), duration_per_image)
    print(f"[*] Video generated at {os.path.join(local_dir, 'movie.mp4')}")

def generate_audio_file(local_dir):
    text_folder = os.path.join(local_dir, 'text')
    audio_folder = os.path.join(local_dir, 'audio')
    os.makedirs(audio_folder, exist_ok=True)

    full_text = ""

    for file_name in sorted(os.listdir(text_folder)):
        if file_name.endswith('.txt'):
            file_path = os.path.join(text_folder, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                full_text += file.read() + " " 

    output_path = os.path.join(audio_folder, 'output.mp3')

    generate_audio(full_text, output_path)

def start_scanning(pages):
    global scan_complete
    try:
        response = requests.get(f'http://192.168.134.198:1337/scan_book?pages={pages}')
        if response.status_code == 200:
            data = response.json()
            folder_name = data.get("folder")
            if folder_name:
                list_response = requests.get(f'http://192.168.134.198:1337/scans/{folder_name}')
                if list_response.status_code == 200:
                    # step 0 dump the scans
                    soup = BeautifulSoup(list_response.text, 'html.parser')
                    files = [a.get('href').split('/')[-1] for a in soup.find_all('a')]
                    
                    # step 1 store the files locally
                    print(f'[*] Extracting the files: {files}')
                    local_dir = create_local_book_folder(folder_name, files, pages)
                    
                    # step 2 extract the  data from the book
                    print(f'[*] Extracting data')
                    extract_data(local_dir)

                    # step 3 generate audio
                    print(f'[*] Generating audio')
                    generate_audio_file(local_dir)

                    # step 4 generate images
                    print(f'[*] Generating imagess')
                    generate_images_from_text_files(local_dir)

                    # step 5 generate video
                    print(f'[*] Generating video')
                    generate_video(local_dir)

                    scan_complete = True
                else:
                    print(f"Error: Failed to list files with status code {list_response.status_code}")
                    scan_complete = False
        else:
            print(f"Error: Scanning request failed with status code {response.status_code}")
            scan_complete = False
    except requests.RequestException as e:
        print(f"Exception occurred: {e}")
        scan_complete = False

@app.route('/add_book')
def add_book():
    global scan_complete
    scan_complete = False 
    pages = request.args.get('pages', 1, type=int)
    
    threading.Thread(target=start_scanning, args=(pages,)).start()
    
    return redirect('/scanning')

@app.route('/scan_status')
def scan_status():
    if scan_complete:
        return {"status": "complete"}
    return {"status": "in_progress"}

@app.route('/scanning')
def scanning():
    return render_template('scanning.html')
   
def create_local_book_folder(folder_name, files, pages):
    book_hash = hashlib.md5(folder_name.encode()).hexdigest()
    book_folder = os.path.join(app.config['UPLOAD_FOLDER'], book_hash)

    os.makedirs(os.path.join(book_folder, 'scans'), exist_ok=True)
    os.makedirs(os.path.join(book_folder, 'video'), exist_ok=True)
    os.makedirs(os.path.join(book_folder, 'text'), exist_ok=True)
    os.makedirs(os.path.join(book_folder, 'audio'), exist_ok=True)

    for file_name in files:
        print('[*] Downloading:', file_name)
        file_url = f'http://192.168.134.198:1337/static/scans/{folder_name}/{file_name}'
        file_response = requests.get(file_url)
        if file_response.status_code == 200:
            file_path = os.path.join(book_folder, 'scans', file_name)
            with open(file_path, 'wb') as f:
                f.write(file_response.content)
                print(" > success")
        else:
            print(f"Error: Failed to download {file_name} with status code {file_response.status_code}")

    # create info file
    info = {
        "Title": "",
        "Author": "",
        "Number of Pages": str(pages),
        "Description": "",
        "Hash": book_hash
    }
    with open(os.path.join(book_folder, 'info.json'), 'w') as f:
        json.dump(info, f, indent=4)

    return book_folder

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context=(cert_path, key_path))
