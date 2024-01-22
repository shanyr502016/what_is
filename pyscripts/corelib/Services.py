
from corelib.Loggable import Loggable
from corelib.Process import Process
from time import sleep
import re
import tempfile
import os
from corelib.SCP import SCP


class WinService(Loggable):
    
    def __init__(self, name: str, path:str, ssh_command: str):

        super().__init__(__name__)
        
        self._name = name
        self._ssh_command = ssh_command
        self._path = path
        self.__w_pid = None
        self._kill_pid = None
        self.__w_state = None
        self.__w_state_id = None
        self._query = 'sc'
        self._stederr = True
        self._servicename = ''
        
        self._sch_without_ssh = None
        self._execfilepath = None
        self._nodes_temp_dir = None
        self._serviceDisplayName = None

    def setQuery(self, query):
        
        self._query = query

    def setServiceName(self, servicename):

        self._servicename = servicename
        
    def setSCPWITHOUTSSH(self, sch_without_ssh):
    
        self._sch_without_ssh = sch_without_ssh
        
    def setExecfilepath(self, execfilepath):
    
        self._execfilepath = execfilepath
        
    def setServiceDisplayName(self, serviceDisplayName):
    
        self._serviceDisplayName = serviceDisplayName
        
    def setNodesTempDIR(self, nodes_temp_dir):
    
        self._nodes_temp_dir = nodes_temp_dir
        
    def setKillPID(self, pid):
    
        self._kill_pid = pid
               
    def start(self):

        if self._query == 'schtasks':
            self._run_sc(['/Change /TN', self._get_service_name(self._name), '/ENABLE'])
            self._run_sc(['/RUN /TN', self._get_service_name(self._name)])
        elif self._query == 'sc':
            self._run_sc(['start', self._get_service_name(self._name)])
        elif self._query == 'handle':
            _schtaskscmd=self._executeSCHTasks(self._name)
            if _schtaskscmd is not None:
                self._run_sc([_schtaskscmd])
        else:
            self._stederr = False
            self._run_sc([self._name])
        sleep(3)
        return self.status()
        
    def stop(self):

        if self._query == 'schtasks':
            self._run_sc(['/END /TN', self._get_service_name(self._name)])  
            self._run_sc(['/Change /TN', self._get_service_name(self._name), '/DISABLE'])            
        elif self._query == 'sc':            
            self._run_sc(['stop', self._get_service_name(self._name)])
        elif self._query == 'handle':
            pid = self.get_status()
            self._run_sc(['taskkill /pid '+ str(pid) + ' /f'])
        elif self._query == 'taskkill':
            self._run_sc(['/pid '+ str(self._kill_pid) + ' /f'])
        else:
            self.log.info(self._get_service_name(self._name))   
        sleep(5)
        return self.status()
        
    def restart(self):
        
        self.log.info('Restart.....')      
       
        
    def status(self):
        return self.get_status()
        
    def _check_sc_status(self): # Check the Windows Service Disabled or available before start/stop/status
        check_args = []
        if self._ssh_command:
            check_args = [self._ssh_command]
        check_args.append('"sc queryex state=all | find \\"SERVICE_NAME\\""')
        output = self.execute_status(check_args)
        if self._name not in [data.split(':')[-1].strip() for data in output]:
            self.log.debug(f'{self._name} service not available')
            return False
        args = []
        if self._ssh_command:
            args = [self._ssh_command]
        args.append('sc qc') 
        args.append(self._get_service_name(self._name))
        output = self.execute_status(args)
        for data in output:
            if 'START_TYPE' in data:
                if 'DISABLED' in data:
                    return False     
        return True
                
    def get_process_id(self):
        result = None
        if self._query == 'schtasks':
            lines = self._run_sc(['/Query /FO LIST /TN', self._get_service_name(self._name)])
            for index, line in enumerate(lines):
                state_match = re.match(r'\s*Status\s*:+(\D+)', line)
                state = re.match(r'\s*Status\s*:+(\D+)', line)
                if state_match:
                    self.__w_state = state.group(1).strip()
                    if self.__w_state == 'Disabled':
                        result = False
                        break
                    elif self.__w_state == 'Running':                        
                        result = True
                        break
        elif self._query == 'sc':
            if not self._check_sc_status():
                result = -1
                return result
            lines = self._run_sc(['queryex', self._get_service_name(self._name)])
            for index, line in enumerate(lines):
                state_match = re.match(r'\s*STATE\s*:\s+([0-9]+)\s+(.+)', line)
                pid = re.match(r'\s*PID\s*:\s+([0-9]+)', line)
                if pid:
                    self.__w_pid = int(pid.group(1))
                    result = int(pid.group(1))
                    break   
        elif self._query == 'handle':
            lines = self._run_sc([self._name])
            for index, line in enumerate(lines): 
                if self._servicename in line:
                    self.log.debug(line.split(',')[1])
                    result = int(line.split(',')[1])
                    break

        return result
                    
                
    def get_status(self):
        pid = self.get_process_id()
        if pid:
            return pid
        return False        
        

    def _validate_result(self, result: int): 
        """
        Validates the result of the service command
        """        
        if result != 0 and result != 1056 and result != 1062:
            if result == 1060 or result == 36:
                
                self.log.info(f" {self._name} Service was not found")  
            self.log.info('An error occured while checking the service (code ' + str(result) + ')')
       
    def _run_sc(self, sc_args):
        if self._ssh_command:
            args = [self._ssh_command]
            if self._query != 'handle':
                args.append(self._query)
        else:
            if self._query != 'handle':
                args = [self._query]
        args.extend(sc_args)
        args = ' '.join([elem for elem in args])
        process = Process(args,self._path)
        process.set_stderr(self._stederr)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        self._validate_result(process.execute())
        return process.get_out_lines()
        
    def _get_service_name(self, service_name: str):
        
        return '\'\"'+ service_name+ '\"\''
       
    def _winprocess(self):
        if self._ssh_command:
            args = [self._ssh_command]
        args.append("'powershell -Command \"Get-WmiObject Win32_Process | Select-Object ProcessID, Name, CommandLine, Path | Format-Table -Property ProcessID, Name, CommandLine, Path -AutoSize -Wrap\"'")
        args = ' '.join([elem for elem in args])
        self.log.info(args)
        process = Process(args,self._path)
        process.set_stderr(self._stederr)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        self._validate_result(process.execute())
        return process.get_out_lines()
        
        
    def _executeSCHTasks(self, name):    

        if self._serviceDisplayName is not None:
            if self._createSCHTasks(self._serviceDisplayName, self._execfilepath) == 0:                
                args = []
                args.append('"cd '+self._nodes_temp_dir+' && '+ self._nodes_temp_dir.split(':')[0]+':'+' && cmd /c '+self._nodes_temp_dir+'/'+ self._serviceDisplayName +'.bat"')           
                return ' '.join([str(elem) for elem in args])
            else:
                self.log.debug("SCHTASK Not Execute")
                return None
        else:
            return None
    
        
    def _createSCHTasks(self, service_name, content):
              
        lines = []
        lines.append(f'SCHTASKS /Query /TN "{service_name}" > nul 2>&1 && (schtasks /run /tn "{service_name}")|| (SCHTASKS /Create /SC ONSTART /TN "{service_name}" /TR "{content}" /RL HIGHEST) && (schtasks /run /tn "{service_name}")')
        file  = tempfile.NamedTemporaryFile('w+t')
        filepath = file.name
        for line in lines:
            file.write(line + '\n')
        file.flush()
        if self._sch_without_ssh:
            result = self._sch_without_ssh.copy_to_remote(filepath,os.path.join(self._nodes_temp_dir,self._serviceDisplayName + '.bat'))
            return result
        return 1
        
        
    def execute_status(self, args):
        args = ' '.join([elem for elem in args])
        process = Process(args,self._path)
        process.set_stderr(self._stederr)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        self._validate_result(process.execute())
        return process.get_out_lines()
        
    def execute(self):
        if self._ssh_command:
            args = [self._ssh_command]
        args.append(self._name)
        args = ' '.join([elem for elem in args])
        self.log.debug(args)
        process = Process(args,self._path)
        process.set_stderr(self._stederr)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        self._validate_result(process.execute())
        return process.get_out_lines()
        
    def execute_with_parallel(self):
        if self._ssh_command:
            args = [self._ssh_command]
        args.append(self._name)
        args = ' '.join([elem for elem in args])
        self.log.debug(args)
        process = Process(args,self._path)
        process.set_parallel_execution(True)
        process.set_stderr(self._stederr)
        return process.execute()
        
        
            


