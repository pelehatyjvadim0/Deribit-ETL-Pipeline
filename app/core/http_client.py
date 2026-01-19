import aiohttp

class HttpClient:
    session: aiohttp.ClientSession | None = None
    
    @classmethod
    def get_session(cls) -> aiohttp.ClientSession | None:
        
        return cls.session