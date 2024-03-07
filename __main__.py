from fastapi import FastAPI
from fileroutes import create_directory_router

app = FastAPI(
    routes=create_directory_router("remote_files")
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)