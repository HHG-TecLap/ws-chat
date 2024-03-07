from os import PathLike
from fastapi.responses import FileResponse
from starlette.routing import Route, BaseRoute
from pathlib import Path

def file_route(root: Path, path: Path) -> Route:
    relative = path.relative_to(root)
    def endpoint():
        return FileResponse(path)
    
    return Route("/" + str(relative), endpoint)

def _make_routes_with_subdirs(path: Path) -> list[Route]:
    routes = []
    for subpath, _, filenames in path.walk():
        for file in filenames:
            filepath = subpath.joinpath(file)
            if not filepath.is_file(): continue
            routes.append(file_route(path, filepath))
    return routes

def _make_routes_without_subdirs(path: Path) -> list[Route]:
    return [
        file_route(path, subpath)
        for subpath in filter(
            lambda p: p.is_file(),
            path.iterdir()
        )
    ]
        
        

def create_directory_router(
    path: PathLike|str,
    include_subdirs: bool=False
) -> list[BaseRoute]:
    path = Path(path)
    if not path.is_dir():
        raise ValueError("Path is not a directory")
    
    if include_subdirs:
        return _make_routes_with_subdirs(path) # type: ignore
    else:
        return _make_routes_without_subdirs(path) # type: ignore