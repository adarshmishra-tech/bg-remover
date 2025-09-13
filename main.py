import os
import asyncio
import torch
import torchvision.transforms as transforms
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import numpy as np

# Global variables
model = None
executor = ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 8))

# Initialize FastAPI app
app = FastAPI(title="AI Clear BG Backend", description="High-performance local U2Net-based API for removing image backgrounds with premium features")

# Rate limiting setup (20 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Render
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Startup event to load model
@app.on_event("startup")
async def startup_event():
    global model
    try:
        model = torch.hub.load('xuebinqin/U-2-Net', 'u2net', pretrained=True)
        model.eval()
        if torch.cuda.is_available():
            model = model.cuda()
        print("U2Net model loaded successfully.")
    except Exception as e:
        print(f"Failed to load U2Net model: {e}")
        raise

# Synchronous image processing
def process_image_sync(contents: bytes, filename: str) -> bytes:
    global model
    if model is None:
        raise ValueError("Model not loaded.")
    
    try:
        image = Image.open(BytesIO(contents)).convert('RGB')
        orig_size = image.size
        input_image = image.resize((320, 320), Image.BILINEAR)
        input_tensor = transforms.ToTensor()(input_image).unsqueeze(0)
        
        device = next(model.parameters()).device
        input_tensor = input_tensor.to(device)
        
        with torch.no_grad():
            outputs = model(input_tensor)
            prediction = outputs[0]
            mask = torch.sigmoid(prediction).squeeze().cpu().numpy()
        
        mask = (mask - mask.min()) / (mask.max() - mask.min())
        mask = (mask > 0.6).astype(np.uint8)
        mask_pil = Image.fromarray(mask * 255).resize(orig_size, Image.LANCZOS)
        
        result_image = image.copy().convert('RGBA')
        result_image.putalpha(mask_pil)
        
        output = BytesIO()
        result_image.save(output, format='PNG', optimize=True)
        output.seek(0)
        return output.read()
    
    except Exception as e:
        raise RuntimeError(f"Image processing failed: {str(e)}")

@app.post("/remove-background")
@limiter.limit("20/minute")
async def remove_background(
    file: UploadFile = File(..., description="Image file to process (JPEG/PNG/WEBP only, max 10MB)")
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail={"error": "Only JPEG, PNG, and WEBP files are supported."})
    
    contents = await file.read()
    
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail={"error": "File size must be less than 10MB."})
    
    try:
        loop = asyncio.get_event_loop()
        processed_bytes = await loop.run_in_executor(
            executor, process_image_sync, contents, file.filename or "image.png"
        )
        
        return StreamingResponse(
            BytesIO(processed_bytes),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=processed_{file.filename or 'image.png'}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": f"Internal server error: {str(e)}"})

@app.on_event("shutdown")
async def shutdown_event():
    executor.shutdown(wait=True)
