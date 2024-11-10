import re
import os
from PIL import Image
import pytesseract
import json
import base64
import ollama
from openai import OpenAI
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_json_from_text(text):
    try:
        json_match = re.search(r'(\{.*?\})', text, re.DOTALL)
        if json_match:
            json_content = json_match.group(1)
            return json_content
        else:
            print("No JSON content found in the text.")
            return None
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {str(e)}")
        return None

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

# def extract_title_and_author_from_image(image_path, additional_text=""):
#     response = ollama.chat(
#         model="llava:13b", 
#         messages=[
#             {
#                 'role': 'system',
#                 'content': """
# You will be provided a book's cover.
# Extract only the Title and the Author name from this Romanian book cover in json format: {"title": "", "author": ""}. 
# Note that the cover will always have the title and author name on separate lines and written with different fonts.
# Do not include the Title in the Name or the Name in the Title. 
# They must be separate. 
# If any of the title or author are not visible, put an empty string in json, however, you must always do your best to extract both the title and name as it is guaranteed that they are present in the cover image provided.
# Do not add anything else to your response. 
# """,
#                 'images': [image_path]
#             },
#             {
#                 'role': 'user',
#                 'content': 'Extract the title and author from this book cover.'+additional_text,
#             }
#         ]
#     )

#     content = response.get('message', {}).get('content', "")
#     print("[*] LLM Response:", content)

#     try:
#         data = json.loads(str(extract_json_from_text(content)))
#         title = data.get("title", "")
#         author = data.get("author", "")
#         return title, author
#     except json.JSONDecodeError:
#         print("Error: Failed to decode JSON response.")
#         return "", ""

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string

def extract_title_and_author_from_image(image_path, prompt="What’s in this image?"):
    base64_image = encode_image_to_base64(image_path)
    img_type = "image/jpeg" 

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": """
You will be provided a book's cover.
Extract only the Title and the Author name from this Romanian book cover in JSON format: {"title": "", "author": ""}. 
Note that the cover will always have the title and author name on separate lines and written with different fonts.
Do not include the Title in the Name or the Name in the Title. 
They must be separate. 
If any of the title or author are not visible, put an empty string in json, however, you must always do your best to extract both the title and name as it is guaranteed that they are present in the cover image provided.
Do not add anything else to your response.
                    """},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{img_type};base64,{base64_image}"},
                    },
                ],
            }
        ],
        max_tokens=300
    )

    print("[*] OpenAI Response:", response.choices[0].message.content)
   
    response = response.choices[0].message.content
    return response


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

# image_path = "cov1.jpeg"
# print('>>',extract_json_from_text(extract_title_and_author_from_image(image_path)))

# image_path = "cov2.jpeg"
# print('>>',extract_json_from_text(extract_title_and_author_from_image(image_path)))

# image_path = "cov3.jpeg"
# res = json.loads(extract_json_from_text(extract_title_and_author_from_image(image_path)))
# print(res["title"], res["author"])
