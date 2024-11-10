from openai import OpenAI

def generate_audio(text, output_path):
    client = OpenAI()

    response = client.audio.speech.create(
        model="tts-1-hd", 
        voice="echo", 
        input=text  
    )

    response.stream_to_file(output_path)
    print(f"[*] Audio saved to {output_path}")