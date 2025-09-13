import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize FastAPI app
app = FastAPI(title="AI Clear BG Backend", description="High-performance API for removing image backgrounds using remove.bg")

# Rate limiting setup (10 requests per minute per IP for high traffic stability)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key from environment variable
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
if not REMOVE_BG_API_KEY:
    raise ValueError("REMOVE_BG_API_KEY environment variable is required")

@app.post("/remove-background")
@limiter.limit("10/minute")  # Scalable rate limit to handle high traffic
async def remove_background(
    file: UploadFile = File(..., description="Image file to process (JPEG/PNG only, max 5MB)")
):
    """
    Async endpoint to remove background from uploaded image.
    Validates file type and size, processes via remove.bg API, returns processed image.
    """
    # Input validation: file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail={"error": "Only JPEG and PNG files are supported."})
    
    # Read file contents asynchronously
    contents = await file.read()
    
    # Input validation: file size (5MB max)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail={"error": "File size must be less than 5MB."})
    
    try:
        # Async HTTP request to remove.bg API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.remove.bg/v1.0/removebg",
                files={
                    "image_file": (
                        file.filename or "image.jpg",
                        contents,
                        file.content_type
                    )
                },
                data={"size": "auto"},
                headers={"X-Api-Key": REMOVE_BG_API_KEY},
            )
        
        # Handle API errors
        if response.status_code != 200:
            error_detail = response.text or "Unknown error from remove.bg API"
            raise HTTPException(status_code=400, detail={"error": f"Background removal failed: {error_detail}"})
        
        # Return processed image as streaming response
        return StreamingResponse(
            iter([response.content]),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=processed_{file.filename or 'image.png'}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": f"Internal server error: {str(e)}"})
