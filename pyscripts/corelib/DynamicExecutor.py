
from corelib.Loggable import Loggable
from corelib.DynamicImporter import DynamicImporter
from argparse import Namespace



class DynamicExecutor(Loggable):
    
    """
    Dynamically Execute the Classes and Functions
    """
    
    def __init__(self, args):
         
        super().__init__(__name__)
        
        """
        Set arguments from Module instance
        """           
        self.__arguments = args._arguments

        """
        Module name from importer
        """   
        self.__module_name = None

        self.__module = None
        """
        Sub Module name from importer
        """
        self.__sub_module_name = None
        """
        Action from module name
        """
        self.__action = None

        self._parallel = False

        self._processesResult = []

        self._environment = []

    def get_module_name(self):  
        """
        Returns the module name exclude sub module name and action
        """      
        return self.__module_name   

    def set_parallel(self, parallel):
        """
        Parallel Execution for targets
        """
        self._parallel = parallel 

    def set_environment(self,environment):
        self._environment = environment

    def get_environment(self):
        return self._environment


        
    def set_module_instance(self, module_name): 
        """
        set targets to filter module name, sub module name and action
        """               
        module = module_name.split('.')  
        self.__module = module 
        
        if len(module) == 1: # Filter Module
            self.__module_name = module_name
            setattr(self.__arguments, 'module', module_name)            
            
        elif len(module) == 2: # Filter sub module
            self.__module_name = module[:-1][0]
            self.__sub_module_name = module[1:][0]         
            
        elif len(module) == 3: # Filter Action
            
            self.__module_name = module[:-2][0]
            
            self.__sub_module_name = module[1:-1][0]
            self.set_sub_module_name(self.__sub_module_name)
            
            self.__action = module[2:][0]
            self.set_action(self.__action)
        elif len(module) == 4: # Filter Action
        
            self.__module_name = module[:-2][0]
            
            self.__sub_module_name = module[1:-1][0]
            
            self.set_sub_module_name(self.__sub_module_name)
            
            self.__action = module[2:][0]
            
            self.set_action(self.__action)
        
            

        
    def get_sub_module_name(self):
        
        return self.__sub_module_name

    def set_sub_module_name(self, sub_module_name):
        
        self.__sub_module_name = sub_module_name  
        
    def get_action(self):
        
        return self.__action      
        
    def set_action(self, action):
        
        self.__action = action    

    def set_process_results(self, results):
        self._processesResult = results    

    def get_process_results(self):
        return self._processesResult
        
    def run_module(self):
        setattr(self.__arguments, 'parallel', self._parallel)
        setattr(self.__arguments, 'callback',(int(getattr(self.__arguments, 'callback')) + 1))    
        self._dynamicImporter = DynamicImporter(self.__arguments)
        self._dynamicImporter._environment = self.get_environment()
        return self._dynamicImporter.execute() 

    def run_class(self):
        setattr(self.__arguments, 'parallel', self._parallel)
        setattr(self.__arguments, 'module', '.'.join(self.__module))
        setattr(self.__arguments, 'callback',(int(getattr(self.__arguments, 'callback')) + 1))
        self._dynamicImporter = DynamicImporter(self.__arguments)
        self._dynamicImporter._environment = self.get_environment()
        return self._dynamicImporter.execute()
    

    def run_service(self, packageinfo, action, module, server='', delta=''):
        extra_args = Namespace(printservice=True)
        args = Namespace(packageinfo=packageinfo, action=action,  module=module, debug=getattr(self.__arguments, 'debug'))
        if server == '':
            args = Namespace(packageinfo=packageinfo, action=action,  module=module, debug=getattr(self.__arguments, 'debug'), delta=delta)
        else:
            args = Namespace(packageinfo=packageinfo, action=action,  module=module, debug=getattr(self.__arguments, 'debug'), server=server, delta=delta)
        self._dynamicImporter = DynamicImporter(args, extra_args)
        return self._dynamicImporter.execute() 
    
    def run_deploy(self, packageinfo, module):
        args = Namespace(debug=getattr(self.__arguments, 'debug'),  module=module,packageid=None,packageinfo=packageinfo)
        self._dynamicImporter = DynamicImporter(args)
        return self._dynamicImporter.execute() 