from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.Constants import Constants
from time import sleep

class StartStopUtilities(Loggable):

        
    def __init__(self, process, action, module_label, is_windows, print_services): 

        super().__init__(__name__)

        self._process = process 
        self._action = action
        self._module_label = module_label
        self._is_windows = is_windows
        self._print_services = print_services

    def _execute_msg(self):
        if self._action == 'Start': 
            return self._start()

        if self._action == 'Stop':
            return self._stop()

        if self._action == 'Status' or self._action == None:
            return self._status()


    def _start(self):

        # Start the Service and print console message    
        result = 1         
        processId = self._process.get_process_id()
        if not processId:                
            if self._is_windows:            
                if self._process.start():
                    result = 0
                else:
                    result = False
            else:
                result = self._process.execute() 
                if self._process.get_parallel_execution():
                    result = 0
                    sleep(5)
            if not self._print_services:
                if result == 0:   
                    processId = self._process.get_process_id()
                    if processId:
                        processId = int(processId)
                    Loggable.log_success(self, f"{self._module_label} is Starting now. {f'PID: {processId}' if type(processId) is int else ''}") 
                else:
                    processId = self._process.get_process_id()
                    self.log.error(f"{self._module_label} is Starting Failed")
            return self._process.get_process_id()          
        else:                
            if not self._print_services:
                if processId == -1:
                    self.log.warning(f"{self._module_label} is Disabled or Not Available.")
                else:
                    self.log.warning(f"{self._module_label} is already Running. {f'PID: {processId}' if type(processId) is int else ''}")
            return processId

    
    def _stop(self):
        # Stop the Service and print console message
        result = 1
        processId = self._process.get_process_id()
        
        if processId == -1:
            self.log.warning(f"{self._module_label} is Disabled or Not Available.")
            return False        
        elif processId:
            if self._is_windows:
                
                if self._process.stop():
                    result = 0              
                else:
                    result = False
            else:                
                result = self._process.execute()     
            if not self._print_services:
                if result == 0:
                    Loggable.log_success(self, f"{self._module_label} is Stopped Successfully")
                else:
                    self.log.error(f"{self._module_label} is Stopped Failed")
            processId = self._process.get_process_id()
            sleep(3)              
            return self._process.get_process_id()            
        else:            
            if not self._print_services:
                if processId == -1:
                    self.log.warning(f"{self._module_label} is Disabled or Not Available.")
                else:
                    self.log.warning(f"{self._module_label} is already stopped")
            return False 

    def _status(self):

        processId = self._process.get_process_id()
        if not self._print_services:
            if processId == -1:
                    self.log.warning(f"{self._module_label} is Disabled or Not Available.")
            elif processId: 
                if type(processId) is str:
                    processId = int(processId)
                self.log.info(Constants.colorize(f"{self._module_label} is Running Successfully!. {f'PID: {processId}' if type(processId) is int else ''}",Constants.TEXT_GREEN))                  
            else:
                self.log.warning(f"{self._module_label} is not Running now")
        return processId
 