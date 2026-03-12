import modal
from pathlib import Path

volume=modal.Volume.from_name("webtime-cache-volume",create_if_missing=True)

#ROOT_DIR=Path(__file__).resolve().parent


image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi",
        "httpx",
        "cachetools",
        "pydantic"
    )
    .add_local_python_source("server","wayback","cache","models")
)
app=modal.App("webtime-backend")
@app.function(
        image=image,
        volumes={"/cache": volume})
@modal.asgi_app()
def fastapi_app():
    import server
    return server.app

