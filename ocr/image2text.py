from PIL import Image
import pytesseract
import json
import base64
import ollama

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def extract_text_from_image(image_path, additional_text=""):
    response = ollama.chat(
        model="llama3.1:latest",  
        messages=[
            {
                'role': 'system',
                'content': 'You are an OCR. You will extract all text from the pro image as it is and do not add anything else to your response:',
            },
            {
                'role': 'user',
                'content': 'Extract text from this image.'+additional_text,
                'images': [image_path]
            }
        ]
    )
    content = response.get('message', {}).get('content', "")
    print("[*] LLM Response:", content)

    return content

def extract_title_and_author_from_image(image_path, additional_text=""):
    response = ollama.chat(
        model="llama3.1:latest", 
        messages=[
            {
                'role': 'system',
                'content': 'You are an OCR. You will extract only the title and author from this book cover in json format: {"title": "", "author": ""} and do not add anything else to your response:',
                'images': [image_path]
            },
            {
                'role': 'user',
                'content': 'Extract the title and author from this book cover.'+additional_text,
            }
        ]
    )

    content = response.get('message', {}).get('content', "")
    print("[*] LLM Response:", content)

    try:
        data = json.loads(content)
        title = data.get("title", "")
        author = data.get("author", "")
        return title, author
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response.")
        return "", ""
    
def extract_title_and_author_from_text(additional_text=""):
    response = ollama.chat(
        model="llama3.1:latest", 
        messages=[
            {
                'role': 'system',
                'content': 'You will extract only the title and author from this book cover in json format: {"title": "", "author": ""} and do not add anything else to your response:',
            },
            {
                'role': 'user',
                'content': 'Extract the title and author from this book cover:'+additional_text,
            }
        ]
    )

    content = response.get('message', {}).get('content', "")
    print("[*] LLM Response:", content)

    try:
        data = json.loads(content)
        title = data.get("title", "")
        author = data.get("author", "")
        return title, author
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response.")
        return "", ""

def split_and_ocr(image_path):
    # Open the image
    img = Image.open(image_path)

    # Get the dimensions of the image
    width, height = img.size

    # Calculate the middle of the image
    middle = width // 2

    # Split the image into left and right halves
    left_half = img.crop((0, 0, middle, height))
    right_half = img.crop((middle, 0, width, height))

    # Perform OCR on both halves
    left_text = pytesseract.image_to_string(left_half)
    right_text = pytesseract.image_to_string(right_half)

    return left_text, right_text

def do_ocr(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text



# # Example usage
# image_path = 'your_image.jpg'
# left_text, right_text = split_and_ocr(image_path)

# # Print the OCR results
# print("Text from the left half:")
# print(left_text)

# print("\nText from the right half:")
# print(right_text)
