import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from fileroutes import create_directory_router
from config_loader import read_config


config = read_config()
    
app = FastAPI(
    title=config["web"]["app_title"],
    routes=create_directory_router(config["web"]["remote_files_loc"])
)

@app.get("/")
def reroute_to_index():
    return RedirectResponse("/index.html", 301)


if __name__ == "__main__":
    import uvicorn
    logging.warning("Running ASGI Server from interpreter. This is unsafe and should only be used for debugging!")
    uvicorn.run(app)