from fastapi import FastAPI
from app import urls
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination

from app.utils import MEDIA_ROOT

app = FastAPI()


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "data": None
        },
    )

# Include the URLs from the urls.py module
app.include_router(urls.router)

# add_pagination(app)


app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
