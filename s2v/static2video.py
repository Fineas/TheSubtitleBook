from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import os

def create_slideshow_with_audio(images, audio_path, output_path, duration_per_image):
    clips = []
    for image_path in images:
        if os.path.exists(image_path):
            clip = ImageClip(image_path, duration=duration_per_image)
            clips.append(clip)
        else:
            print("Warning: Image file "+image_path+" not found")

    video = concatenate_videoclips(clips, method='compose')

    if os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        audio = audio.volumex(1.0)
    else:
        print("Error: Audio file "+audio_path+" not found")
        return

    video = video.set_audio(audio)

    video_duration = len(images) * duration_per_image
    final_duration = min(video_duration, audio.duration)
    video = video.set_duration(final_duration)

    video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')

# if __name__ == "__main__":
#     images = ["../t2i/image1.jpeg", "../t2i/image2.jpeg"]  # Add paths to your images here
#     audio_path = "../t2s/output.mp3"  # Add path to your audio file here
#     output_path = "output_video.mp4"  # Output video file path
#     duration_per_image = 22  # Duration each image will be displayed in seconds

#     create_slideshow_with_audio(images, audio_path, output_path, duration_per_image)