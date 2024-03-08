from pathlib import PurePath
from os import PathLike

def relative_to_file(path: PathLike|str) -> PurePath:
    return PurePath(__file__).parent.joinpath(path)