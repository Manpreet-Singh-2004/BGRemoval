from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import APIKeyHeader
from rembg import remove
from PIL import Image
from imagekitio import ImageKit
import io
import os

app = FastAPI(title="Canadian Cart BG Remover & Uploader")

# 1. SECRETS
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "super-secret-key-change-in-production")
header_scheme = APIKeyHeader(name="X-Service-Key")

# 2. INITIALIZE IMAGEKIT 
# v5 syntax strictly requires only the private key for server-side auth
imagekit = ImageKit(
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY")
)

def verify_internal_service(api_key: str = Depends(header_scheme)):
    if api_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Unauthorized service access."
        )
    return True

@app.post("/remove-background")
def remove_image_background(
    file: UploadFile = File(...), 
    is_authorized: bool = Depends(verify_internal_service)
):
    try:
        # 1. Validate File
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image.")

        # 2. Process Image (rembg)
        image_bytes = file.file.read()
        input_image = Image.open(io.BytesIO(image_bytes))
        output_image = remove(input_image)

        # 3. Convert output back to raw bytes (No Base64 needed!)
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG')

        # 4. Upload to ImageKit using direct bytes
        upload_response = imagekit.files.upload(
            file=img_byte_arr.getvalue(),
            file_name=f"nobg_{file.filename}",
        )

        # 5. Return the direct URL
        return {
            "success": True,
            "url": upload_response.url,
            "fileId": upload_response.file_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing or upload failed: {str(e)}")