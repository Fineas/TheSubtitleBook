from diffusers import StableDiffusionPipeline
import torch

# Load the Stable Diffusion model from Hugging Face
pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4")
pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

# Generate an image from a text prompt
prompt = "A fantasy landscape with mountains and rivers at sunrise mid20th century Disney style"
image = pipe(prompt).images[0]

# Save the image
image.save("output.png")