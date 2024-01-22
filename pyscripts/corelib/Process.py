
import os
import sys
from signal import SIGKILL
from subprocess import Popen, PIPE, STDOUT, run
import threading
import re
from time import sleep
from corelib.Loggable import Loggable
from corelib.ThreadFactory import ThreadFactory


class Process(Loggable, metaclass=ThreadFactory):


    def __init__(self, process_args, working_path = os.getcwd(), ssh_command = ''):

        super().__init__(__name__)

        self.__process = None # Process Object subprocess.Popen
       
        self.__pid = None
        
        self.__epid = None
        
        if working_path == '':
            self.__working_directory = os.getcwd()
        else:
            self.__working_directory = working_path
        """ Working directory that should be used for the process """
        
        self.__process_args = process_args
        """ Process name and arguments for executing """
    
        self.__service_name = None
        
        self.__ssh_command = ssh_command
        
        
        self.__env = os.environ.copy()
        """ Environment variables for the process"""
        
        
        self.__use_shell = True
        """ Controls if the process should be executed in a shell environment"""
        
        self.__timeout = ProcessTimeout(self.log, self)
        
        self.out = ''
        """ Raw output of the process"""
        
        self.err = ''
        
        self.__collect_output = False
        """ When True, the output will be redirected to a local variable"""
        
        self.__ignore_errors = False
        """ Indicates if the return value of the process should throw an exception or not"""        
        
        self.__print_output = False
        """ Controls if the process output should be printed to the console"""
        
        self.__command_regex = None
        
        self.__service_regex = None

        self._timeout_kill = None
        
        self.__action = None
        
        self.__process_wait = None
        
        self.__parallel = False

        self.__ppid = False

        self.__stderr = True

        self.__error_check = True
               
        
    def set_command_regex(self, regex: str):
        
        self.__command_regex = regex
        
    def set_service_regex(self, regex: str):
        
        self.__service_regex = regex
        
    def set_action(self, action: str):
        
        self.__action = action

    def set_shell(self, shell):

        self.__use_shell = shell
        
    def set_timeout(self, timeout: int):
        
        self.__timeout.set_timeout(timeout)
        self._timeout_kill = timeout
        
    def set_servicename(self, service_name):
        
        self.__service_name = service_name
        
    def set_parallel_execution(self, parallel: bool):
        
        self.__parallel = parallel
        
    def get_parallel_execution(self):    
        return self.__parallel
    
    def get_error_check(self):

        return self.__error_check

    def set_ppid(self, ppid: bool):

        self.__ppid = ppid

    def set_stderr(self, stderr):

        self.__stderr = stderr

    def set_error_check(self, error_check):

        self.__error_check = error_check

    def thread_execute(self, process_list, process_function):

        try:
            threads = []
            for _index,process in enumerate(process_list):
                thread = threading.Thread(target=process_function, args=(process,process_list[_index]['label']))
                sleep(.2)
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()

        except Exception as exp:
            self.log.error(exp) 


    def execute(self):

        """
        Execute the process
        """
        self.log.debug("Working Directory: "+self.__working_directory)
        self.log.debug("Process args: " + str(self.__process_args))       
        
        pipe_stdio = self.__collect_output or self.__print_output is None

        args = {
            'args': self.__process_args, 'env':  self.__env, 'cwd': self.__working_directory, 'shell': self.__use_shell
        }
        
        args['stdout'] = PIPE
        if self.__stderr:
            args['stderr'] = STDOUT
        args['stdin'] = PIPE
        args['universal_newlines'] = False
        args['bufsize'] = 1       
        
        
        self.__process = Popen(**args)
        self.__epid = self.__process.pid

        if pipe_stdio:
            for std_out_line in iter(self.__process.stdout.readline, b''):                        
                line = std_out_line.decode('utf-8', 'backslashreplace')
                self.out += line
        self.__timeout.start()
        
        if self.__parallel:
            return self.__process
        self.__process_wait = self.__process.wait()
        
        result = 0
        
        if pipe_stdio == False:
            with self.__process.stdout:
                if 'nohup' in self.__process_args:
                    self.log.debug('Turn on Background process')
                    sleep(5)
                    return 0
                if len(self.log_subprocess_output(self.__process.stdout)) > 0:
                    if self.__error_check:
                        self.log.error('Error Found')
                        result = 1
                    else:
                        result = self.__process.poll()
                        return result
                else:
                    result = self.__process.poll()


        if pipe_stdio == False:
            self.log.debug("Execution Process ID: "+ str(self.__epid))
            if self.__command_regex:
                if self.__pid:
                    self.log.info("PID: "+ str(self.__pid))
        self.__timeout.stop()
                    
        self.kill()          

        if self.__process.returncode != 0:
            self.log.error("Execution Failed")
        # else:
        #     if pipe_stdio == False:
        #         Loggable.log_success(self, "Execution Success")       

        return result   
       
    
    def kill(self):

        if self.__action == 'Stop':            
            if self.__command_regex:
                sleep(8)
                pid = self.get_process_id()
                if pid:                
                    self.kill_service(pid)
            if self.__service_regex:
                sleep(8)
                pid = self.get_process_id()
                if pid:                
                    self.kill_service(pid)
                

    
    def get_process_id(self):
        command = None
        result = None
        
        if self.__ssh_command:
            command = self.__ssh_command + ' ps -eo pid,ppid,command --width 4000 | grep '+ self.__service_name
        else:
            command = 'ps -eo pid,ppid,command --width 4000 | grep '+ self.__service_name   
        args = {
            'args': command, 'env':  self.__env, 'cwd': os.getcwd(), 'shell': self.__use_shell
        }

        self.log.debug("Process args: " + str(command))
        
        args['stdout'] = PIPE
        args['stderr'] = STDOUT
        args['stdin'] = PIPE
        args['universal_newlines'] = False
        args['bufsize'] = 1        
        
        pid_process = Popen(**args)
        out, err = pid_process.communicate()

        for cmd_line in out.decode('utf-8').splitlines():
            if self.__ppid:
                if self.__service_regex:
                    ppid = cmd_line.split()[1]
                    if cmd_line.split()[1] == '1':
                        ppid = cmd_line.split()[0]
                        for pwdx in self.get_pwdx(ppid):
                            if re.search(self.__service_regex, pwdx):
                                result = pwdx.split(':')[0]
                                break
            else:
                if self.__command_regex:
                    if re.search(self.__command_regex, cmd_line):                
                        result = cmd_line.split()[0]
                        break  
                else:
                    if cmd_line.split()[1] == '1':
                        result = cmd_line.split()[0]
                        break         
        return result
        
    def killPID(self, pid):       
        # Killing DeadProcess ID's
        if pid is not None:
            if self.__ssh_command:
                command = self.__ssh_command + ' kill -9 ' + pid
                args = {'args': command, 'env':  self.__env, 'cwd': os.getcwd(), 'shell': self.__use_shell}
                args['stdout'] = PIPE
                args['stderr'] = STDOUT
                args['stdin'] = PIPE
                args['universal_newlines'] = False
                args['bufsize'] = 1 
                self.log.debug(f"PID for SSH {command}")
                kill_process = Popen(**args)
                out, err = kill_process.communicate()
                return out.decode('utf-8').splitlines()
            else:                
                self.log.debug("PID for Kill: "+ str(pid))
                return os.kill(int(pid), SIGKILL)         
        
    def kill_service(self, pid):        
    
        if self.__ssh_command:
            command = self.__ssh_command + ' kill -9 ' + pid
            args = {
            'args': command, 'env':  self.__env, 'cwd': os.getcwd(), 'shell': self.__use_shell
            } 
            args['stdout'] = PIPE
            args['stderr'] = STDOUT
            args['stdin'] = PIPE
            args['universal_newlines'] = False
            args['bufsize'] = 1 
            self.log.debug(f"PID for SSH {command}")
            kill_process = Popen(**args)
            out, err = kill_process.communicate()            
            return out.decode('utf-8').splitlines()
        else:
            os.kill(int(pid), SIGKILL)
            self.log.debug("PID for Kill: "+ str(pid))
            return self.get_process_id()
            
        
    def get_pwdx(self, pid):

        if self.__ssh_command:
            command = self.__ssh_command + ' pwdx '+ pid
        else:
            command = 'pwdx '+ pid   
        args = {
            'args': command, 'env':  self.__env, 'cwd': os.getcwd(), 'shell': self.__use_shell
        }       
        
        args['stdout'] = PIPE
        args['stderr'] = STDOUT
        args['stdin'] = PIPE
        args['universal_newlines'] = False
        args['bufsize'] = 1 
        
        pwdx_process = Popen(**args)
        out, err = pwdx_process.communicate()
            
        return out.decode('utf-8').splitlines()
        
      
    def hide_output(self):
        """
        Disables printing the stdout/err of the process
        """
        self.__print_output = False
        
        
    def ignore_errors(self):
        """
        Disables the validation of the return value of the process execution.
        """
        self.__ignore_errors = True
        
    def collect_output(self):
        """
        Enables stdout collecting. This will redirect the stdout/err of the process to a local stream.
        The result is available in "out".
        """
        self.__collect_output = True
            
    def get_out_lines(self):
        """
        Returns the process output, split by lines
        
        :return: lines
        :rtype: List[str]
        """
        return self.out.splitlines()
    
    def get_raw_out_lines(self):
        """
        Returns the process raw output
        
        :return: lines
        :rtype: List[str]
        """
        return self.out
    def get_raw_process(self):  
        
        return self.__process  
    
    def get_pid(self):        
        """
        Returns the pid of the last running process        
        """
        return self.__pid

    def log_subprocess_output(self, pipe):
        """
        Prints the std out from process execution
        """  
        errorLine = []
        for std_out_line in iter(pipe.readline, b''):
            if std_out_line.decode('utf-8').rstrip().__ne__(''):

                if re.search(r"error",std_out_line.decode('utf-8').rstrip().lower()):
                    if self.__error_check:
                        self.log.error(std_out_line.decode('utf-8').rstrip())
                    else:
                        self.log.debug(std_out_line.decode('utf-8').rstrip())
                    errorLine.append(std_out_line.decode('utf-8').rstrip())
                elif re.search(r"fail",std_out_line.decode('utf-8').rstrip().lower()):
                    if self.__error_check:
                        self.log.error(std_out_line.decode('utf-8').rstrip())
                    else:
                        self.log.debug(std_out_line.decode('utf-8').rstrip())
                    errorLine.append(std_out_line.decode('utf-8').rstrip())
                else:
                    self.log.debug(std_out_line.decode('utf-8').rstrip())
                if self._timeout_kill:
                    sleep(self._timeout_kill)
                    exit()
        return errorLine
               
class ProcessTimeout:
    
    def __init__(self, log, process: Process):
        

        self.log = log
        self.__process = process
        self.__timeout = 0
        self.__timeout_condition = threading.Condition()
        self.__timeout_thread = None




    def start(self):
        if self.__timeout <= 0:
            return

        self.log.debug('Timeout ' + str(self.__timeout) + 'sec')
        self.__timeout_thread = threading.Thread(target=self.__wait_timeout, name='process-timeout')
        self.__timeout_thread.start()
        
        
    def set_timeout(self, timeout: int):              
        self.__timeout = timeout
        
       
    def stop(self):
        """
        Stops the process timeout
        """
        self.__timeout_condition.acquire()
        self.__timeout_condition.notify_all()
        self.__timeout_condition.release()
        self.__timeout_thread = None


    def __wait_timeout(self):
        
        
        self.__timeout_condition.acquire()
        self.__timeout_condition.wait(self.__timeout)
        self.__timeout_condition.release()

        process = self.__process.get_raw_process()
        if process is None:
            return
        
        self.log.debug(f"PID: {self.__process.get_process_id()}")
        self.log.debug("Timeout the command and expired")
        self.log.debug("Terminating the whole process")
        return

