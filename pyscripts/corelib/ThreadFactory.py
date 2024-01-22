import threading


class ThreadFactory(type):
    
    factory_map = {}
    
    
    def __call__(cls, *args, **kwargs):
        
        factory = ThreadFactory.factory_map.get(threading.get_ident())
        
        if factory is None:
            
            return super().__call__(*args, **kwargs)
        
        return factory(super(), *args, **kwargs)
        
    @classmethod
    def add(mcs, factory_call):
        ThreadFactory.factory_map[threading.get_ident()] = factory_call
        
        
    @classmethod
    def remove(mcs):
        del ThreadFactory.factory_map[threading.get_ident()]
    
    