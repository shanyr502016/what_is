""" System Executor """

import os
import uuid
from corelib.Loggable import Loggable
from corelib.File import BaseFile, File, Directory
from corelib.Constants import Constants
from corelib.SCP import SCP
from corelib.Process import Process
from corelib.RemoteExecutor import RemoteExecutor

class SystemExecutor(Loggable):

    def __init__(self, args, server_info, environment_provider):
    
        super().__init__(__name__)

        self._arguments = args

        self.server_info = server_info
    
        self.__ssh_command = None
        
        self.__is_linux = None
        
        self.__is_windows = None
        
        self.__environment_provider = environment_provider # Get the Environment Provider method. Reusable method derived
        
        self.server_info = server_info
        
        self.exception = None
        
        
    def update_host_info(self):
    
        self.__ssh_command = self.__environment_provider.get_ssh_command(self.server_info)
        # self.__scp_command = self.__environment_provider.get_ssh_command(self.server_info, True)
        self.__is_windows = self.__environment_provider.is_windows(self.server_info['OS_TYPE'])
        self.__is_linux = self.__environment_provider.is_linux(self.server_info['OS_TYPE'])
        
        
    def execute(self, command_with_path, env_vars={},  execution_location='', error_keywords=['Error', 'Failure'], success_keywords=[],  custom_exception=Exception):
        
        self.update_host_info()
        
        # stdout = None
        # stderr = None
        output_lines = []
        error_lines = []
        exit_code = 1
    
        if self.__ssh_command:
        
            if self.__is_windows:
            
                self.log.debug("Remote Windows")
                
                _remote_executor = RemoteExecutor(self._arguments, self.server_info, self.__environment_provider) 
                self.log.debug(f"Execution Command: {command_with_path}")
                exit_code, stdout, stderr = _remote_executor.execute_ps_with_mount_drive(command_with_path, execution_location=execution_location, env_vars=env_vars, error_keywords=error_keywords, success_keywords=success_keywords, custom_exception=custom_exception) 
                
                
                return exit_code, stdout, stderr
            
            if self.__is_linux:               
            
                self.log.debug("Remote Linux")
            
        else:
        
            if self.__is_windows:
            
                self.log.debug("Local Windows")
            
            
            if self.__is_linux:
            
                self.log.debug("Execute Linux Environment")
                
                command = ''
                for env_var in env_vars:
                    command+= f'export {env_var}={env_vars[env_var]} && '
                command+= f'{command_with_path}'
                           
                process = Process(command)
                process.hide_output()
                process.collect_output()
                process.ignore_errors()
                exit_code = process.execute()                
                stdout = process.get_out_lines()
                output, error = self.log_output(stdout, output_lines, error_lines, success_keywords, error_keywords, custom_exception)
                return exit_code, output, error
        #if stdout:
            

        #exit_code = stdout.channel.recv_exit_status()
        #return exit_code, output_lines, error_lines
        
        # if stdout:
        #     try:
        #         for line in stdout:        
        #             # Exception Handling with Error Keywords
        #             if error_keywords and any(keyword for keyword in error_keywords if keyword.split('::')[0] in line.strip()):                            
        #                 error_lines.append(line.strip())
                        
        #                 if any(len(keyword.split('::')) > 1 and 'skip' in keyword.split('::')[1].lower() and keyword.split('::')[0] in line.strip() for keyword in error_keywords):
        #                     self.log.debug(line.strip())
        #                 else:
        #                     self.log.error(line.strip())
                              
        #                 for keyword in error_keywords:
        #                     if len(keyword.split('::')) > 1:
        #                         if 'return' in keyword.split('::')[1].lower():
        #                             _error_code = 1
        #                             if len(keyword.split('::')) > 2:
        #                                 _error_code = keyword.split('::')[2]
        #                             raise custom_exception(line.strip(), _error_code) # Raise Exception with Error Code
        #             # Exception Handling with Success Keywords
        #             elif success_keywords and any(keyword in line.strip() for keyword in success_keywords):
        #                 self.log.info(Constants.colorize(f"{line.strip()}",Constants.TEXT_GREEN))
        #             # debug message
        #             else:
        #                 self.log.debug(line.strip())  
        #             output_lines.append(line.strip())
                
        #     except custom_exception:
        #         raise  # Re-raise the custom exception
            # except Exception as e:
            #     self.log.error(e)
            #     return stdout
                
            
        #return exit_code, output_lines, error_lines


    def log_output(self, stdout, output_lines, error_lines, success_keywords, error_keywords, custom_exception):
        try:
            if stdout:
                for line in stdout:
                    # Exception Handling with Error Keywords
                    if error_keywords and any(keyword for keyword in error_keywords if keyword.split('::')[0] in line.strip()):
                        error_lines.append(line.strip())

                        if any(len(keyword.split('::')) > 1 and 'skip' in keyword.split('::')[1].lower() and keyword.split('::')[0] in line.strip() for keyword in error_keywords):
                            self.log.debug(line.strip())
                        else:
                            self.log.error(line.strip())
                        for keyword in error_keywords:
                            if len(keyword.split('::')) > 1:
                                _error_code = 1
                                if len(keyword.split('::')) > 2:
                                    _error_code = keyword.split('::')[2]
                                    raise custom_exception(line.strip(), _error_code) # Raise Exception with Error Code
                    # Exception Handling with Success Keywords
                    elif success_keywords and any(keyword in line.strip() for keyword in success_keywords):
                        self.log.info(Constants.colorize(f"{line.strip()}",Constants.TEXT_GREEN))
                    # debug message
                    else:
                        self.log.debug(line.strip()) 
                    output_lines.append(line.strip())
                return output_lines, error_lines
        except custom_exception:
            raise  # Re-raise the custom exception
    
    def copy_files(self,  source_path, destination_path):
        try:
            self.update_host_info()
            if self.__ssh_command:

                if self.__is_windows:
                    self.log.debug("Remote Windows")

                if self.__is_linux:
                    self.log.debug("Remote Linux")
            else:

                if self.__is_windows:
                    self.log.debug("Local Windows")

                if self.__is_linux:

                    _scp = SCP(self.__environment_provider.get_ssh_command(self.server_info, True))

                    self.log.debug("Execute Linux")
                    exit_code = _scp.copy_to_local(source_path, destination_path)
                    return exit_code
               

        except Exception as e:
            self.log.error(e)


    def rsync_files(self, source_path, destination_path, excludes=[]):
        try:
            self.update_host_info()
            if self.__ssh_command:

                if self.__is_windows:
                    self.log.debug("Remote Windows")

                if self.__is_linux:
                    self.log.debug("Remote Linux")
            else:

                if self.__is_windows:
                    self.log.debug("Local Windows")

                if self.__is_linux:

                    _scp = SCP(self.__environment_provider.get_ssh_command(self.server_info, True))

                    self.log.debug("Execute Linux")
                    exit_code = _scp.rsnyc_to_local(source_path + '/*', destination_path + '/', exclude=excludes)
                    return exit_code
        except Exception as e:
            self.log.error(e)
        

    def check_file_exists(self, file_path):

        self.update_host_info()
    
        if self.__ssh_command:
        
            if self.__is_windows:
            
                self.log.debug("Remote Windows")

                _remote_executor = RemoteExecutor(self._arguments, self.server_info, self.__environment_provider) 
                
                result = _remote_executor.remote_check_file_exists(file_path) 
                
                return result
            
            if self.__is_linux:                
            
                self.log.debug("Remote Linux")
            
        else:
        
            if self.__is_windows:
            
                self.log.debug("Local Windows")
            
            
            if self.__is_linux:
            
                self.log.debug("Execute Linux Environment")


    def create_directory_if_not_exists(self, directory_path):
    
        self.update_host_info()
        stdout = None
        output_lines = []
        error_lines = []
        exit_code = 1
        
        if self.__ssh_command:
        
            if self.__is_windows:
            
                self.log.debug("Remote Windows")
                _remote_executor = RemoteExecutor(self._arguments, self.server_info, self.__environment_provider) 
                
                exit_code, stdout, stderr = _remote_executor.create_directory_if_not_exists(directory_path) 
                
                return exit_code, stdout, stderr
            
            if self.__is_linux:
            
                self.log.debug("Remote Linux")
            
        else:
        
            if self.__is_windows:
            
                self.log.debug("Local Windows")      
            
            if self.__is_linux:
                try:
                    args = [] 
                    self.log.debug("Execute Linux Environment")
                    args.append(f"mkdir -p {directory_path}" ) 
                    args = ' '.join([str(elem) for elem in args])
                    process = Process(args)
                    process.hide_output()
                    process.collect_output()
                    process.ignore_errors()
                    exit_code = process.execute()
                    stdout = process.get_out_lines()
                    for line in stdout: 
                        output_lines.append(line.strip())
                    return exit_code, output_lines, error_lines
                except Exception as e:
                    self.log.error(e)
                    return 1
                    