import os
from rembg import remove
from PIL import Image

input_path = "pen.jpeg"
output_path = "penoutput.png"

print("Starting process...")

# Check if file exists
if not os.path.exists(input_path):
    print("Image not found.")
else:
    try:
        print("Image found, removing background...")

        input_image = Image.open(input_path)
        output_image = remove(input_image)

        output_image.save(output_path)

        print("Process completed.")

    except Exception as e:
        print("Something went wrong:", e)