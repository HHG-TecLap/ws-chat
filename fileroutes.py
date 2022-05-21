import os
from aiohttp import web
from typing import Union

def cached_file_getter_factory(routes: web.RouteTableDef, route_path: str, filepath: str, caching : Union["CachingBase",None]):
    wrapper = file_getter_factory(routes,route_path,filepath)
    if caching is not None:
        wrapper = caching.wrap_caching(wrapper)
        pass

    return wrapper
    pass

def file_getter_factory(routes: web.RouteTableDef, route_path: str, filepath: str):
    @routes.get(route_path)
    async def file_listener(request):
        return web.FileResponse(filepath)
        pass

    return file_listener 
    pass

def add_file_routes(routes : web.RouteTableDef, top_path : str,*, recursive : bool = False, caching_system : Union["CachingBase",None] = None, leave_out_top : bool = False):
    filepaths : list[str] = []
    if recursive:
        for path, dirnames, filenames in os.walk(top_path):
            for name in filenames:
                filepaths.append(os.path.join(path,name))
                pass
            pass
        pass
    else:
        for name in os.listdir(top_path):
            path = os.path.join(top_path,name)
            if os.path.isfile(path): filepaths.append(os.path.join(top_path,name))
            pass
        pass

    for path in filepaths:
        start_path = os.path.dirname(top_path) if not leave_out_top else top_path
        relpath = os.path.relpath(path,start_path).replace("\\","/")
        route_path = "/"+relpath

        cached_file_getter_factory(routes,route_path,path,caching_system)
        pass
    pass


from time import perf_counter
class CachingBase:
    __slots__ = "__cache__",
    def __init__(self):
        self.__cache__ : dict = {}
        pass

    def wrap_caching(self, func):
        raise NotImplementedError("When creating a subclass, implement this method")
        pass
    pass

class TimedCache:
    __slots__ = "__cachetimeout__",

    def __init__(self, timeout : float = 300):
        self.__cachetimeout__ = timeout
        self.__cache__ : dict = {}
        
        CachingBase.__init__(self)
        pass

    def wrap_caching(self, func):
        async def wrapper():
            try:
                last_call_time, response = self.__cache__[func]
                if perf_counter() - last_call_time > self.__cachetimeout__: raise KeyError
            except KeyError:
                response = await func()
                self.__cache__[func] = perf_counter(), response
                pass

            return response
            pass

        return wrapper
        pass
    pass

class SizedCache(CachingBase):
    __slots__ = "__max_cache_size__",

    def __init__(self, max_size : int = 20):
        self.__max_cache_size__ = max_size

        CachingBase.__init__(self)
        pass

    def get_size(self) -> int:
        return len(self.__cache__.items())
        pass

    def clean_cache(self):
        items_to_be_removed = max(len(self.__cache__) - self.__max_cache_size__,0)
        if items_to_be_removed < 1:
            return
            pass

        for key, value in sorted(self.__cache__.items(),key=lambda item: item[1][0])[:items_to_be_removed]:
            self.__cache__.pop(key)
            pass
        pass

    def wrap_caching(self, func):
        async def wrapper():
            try:
                response = self.__cache__[func][1]
            except KeyError:
                response = await func()
                self.__cache__[func] = perf_counter(), response
                self.clean_cache()
                pass

            return response
            pass

        return wrapper
        pass
    pass