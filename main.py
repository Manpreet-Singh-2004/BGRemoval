from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import APIKeyHeader
from rembg import remove
from PIL import Image
from imagekitio import ImageKit
import io
import os

# 1. FAIL-FAST STARTUP CHECK
# If AWS fails to inject the ImageKit key, the server crashes immediately 
# rather than failing silently when a user tries to upload.
IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY")
if not IMAGEKIT_PRIVATE_KEY:
    raise RuntimeError("CRITICAL: IMAGEKIT_PRIVATE_KEY environment variable is missing.")

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "super-secret-key-change-in-production")
header_scheme = APIKeyHeader(name="X-Service-Key")

imagekit = ImageKit(private_key=IMAGEKIT_PRIVATE_KEY)

app = FastAPI(title="Canadian Cart BG Remover & Uploader")

# 2. THE AWS HEALTH CHECK
# The Load Balancer will ping this constantly. DO NOT protect it with a key.
@app.get("/health")
def health_check():
    return {"status": "healthy"}

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
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image.")

        # Process Image 
        image_bytes = file.file.read()
        input_image = Image.open(io.BytesIO(image_bytes))
        output_image = remove(input_image)

        # Convert output to PNG bytes
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG')

        # 3. FIX THE EXTENSION BUG
        # Strip the old extension (.jpg, .jpeg) and force .png
        original_name_without_ext = file.filename.rsplit('.', 1)[0]
        safe_filename = f"nobg_{original_name_without_ext}.png"

        # Upload to ImageKit
        upload_response = imagekit.files.upload(
            file=img_byte_arr.getvalue(),
            file_name=safe_filename,
        )

        return {
            "success": True,
            "url": upload_response.url,
            "fileId": upload_response.file_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing or upload failed: {str(e)}")