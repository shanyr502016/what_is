"""Exception Handler"""
import re

class BMIDEException(Exception):

    def __init__(self, message, error_code=1):
    
        super().__init__(message)        
        self.error_code = error_code
        self.message = message
        
    def __str__(self):
    
        return f"BMIDE Exception: {self.message}, Error Code: {self.error_code}"
        
class DLLsException(Exception):

    def __init__(self, message, error_code=1):
    
        super().__init__(message)        
        self.error_code = error_code
        self.message = message
        
    def __str__(self):
    
        return f"DLLs Exception: {self.message}, Error Code: {self.error_code}"
    
class ITKException(Exception):

    def __init__(self, message, error_code=1):
    
        super().__init__(message)        
        self.error_code = error_code
        self.message = message
        
    def __str__(self):
    
        return f"ITK Exception: {self.message}, Error Code: {self.error_code}"
    
class PackageException(Exception):

    def __init__(self, message, error_code=1):
    
        super().__init__(message)        
        self.error_code = error_code
        self.message = message
        
    def __str__(self):
    
        return f"Package Exception: {self.message}, Error Code: {self.error_code}"

