from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from rembg import remove
from PIL import Image
import io
import os


app = FastAPI(title="Canadian Cart BG Remover")

# The secret key shared ONLY between Next.js and Python
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "super-secret-key-change-in-production")
header_scheme = APIKeyHeader(name="X-Service-Key")

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
    is_authorized: bool = Depends(verify_internal_service) # Gatekeeper check
):
    try:
        # File type validation is still good practice here
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image.")

        image_bytes = file.file.read()
        input_image = Image.open(io.BytesIO(image_bytes))

        # Heavy AI processing
        output_image = remove(input_image)

        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return StreamingResponse(img_byte_arr, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")