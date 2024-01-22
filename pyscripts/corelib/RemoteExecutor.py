"""Remote Executor"""
import os
import uuid
from corelib.Loggable import Loggable
from corelib.File import BaseFile, File, Directory
from corelib.SSHConnection import SSHConnection
from corelib.Constants import Constants

class RemoteExecutor(Loggable):

    def __init__(self, args, server_info, environment_provider):
    
        super().__init__(__name__)

        self._arguments = args

        self.server_info = server_info
        
        self.__ssh_command = None
        
        self.__is_linux = None
        
        self.__is_windows = None
        
        self.environment_provider = environment_provider # Get the Environment Provider method. Reusable method derived
        
        self.exception = None

    def update_host_info(self):
    
        self.__ssh_command = self.environment_provider.get_ssh_command(self.server_info)
        # self.__scp_command = self.__environment_provider.get_ssh_command(self.server_info, True)
        self.__is_windows = self.environment_provider.is_windows(self.server_info['OS_TYPE'])
        self.__is_linux = self.environment_provider.is_linux(self.server_info['OS_TYPE'])
    
    
    def create_mount_password(self, mount_pass_file_with_path, remote_script_path=''):

        ssh_client = SSHConnection(self.server_info['USERNAME'],self.server_info['HOSTNAME']) # ssh connection established
        
        _system_keepass = getattr(self._arguments, '_keepass')[self.environment_provider.get_environment_name()][0]['entries']
        _system_keepass_data = next((item for item in _system_keepass if item['title'] == self.server_info['HOSTNAME']), None)

        windows_os_password = _system_keepass_data['password']
   
        if self.__is_windows:
            lines = []
            lines.append(f'$File = "{mount_pass_file_with_path}"')
            lines.append('[Byte[]] $key = (1..16)')
            lines.append(f'$Password = "{windows_os_password}" | ConvertTo-SecureString -AsPlainText -Force')
            lines.append('$Password | ConvertFrom-SecureString -key $key | Out-File $File')
            content = '\n'.join(lines) + '\n'
           
            if remote_script_path == '':
                remote_script_path = os.path.join(os.path.dirname(mount_pass_file_with_path),str(uuid.uuid4()).replace('-', '_')+'.ps1')
                remote_script_path = remote_script_path.replace('/', '\\')
            
            _create_file = File(remote_script_path).remote_write_new_file(ssh_client, content)
            
            ssh_connection = ssh_client.connect()
            
            # Run the uploaded PowerShell script remotely
            stdin, stdout, stderr = ssh_connection.exec_command(f'powershell.exe -File {remote_script_path}')
        
            for line in stdout:
                self.log.debug(line.strip())
            for line in stderr:
                self.log.error(line.strip())

            # Check the exit status
            exit_status = stdout.channel.recv_exit_status()

            ssh_connection.exec_command(f'del {remote_script_path}')
            
            ssh_client.close()

            if exit_status == 0:
                self.log.debug("Mount Drive Encrypted Key Generated!")
                return exit_status
            else:
                self.log.error("Mount Drive Encrypted Key Generated Failed!")
                return 1
                
                
    def execute_ps_with_mount_drive(self, command_with_path, remote_script_path='', execution_location='', env_vars={}, error_keywords=['Error', 'Failure'], success_keywords=[],  custom_exception=Exception):

        self.update_host_info()
        if self.__is_windows:           

            ssh_client = SSHConnection(self.server_info['USERNAME'],self.server_info['HOSTNAME']) # ssh connection established
        
            mount_pass_file_with_path = self.server_info['MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH']
            

            if self.create_mount_password(mount_pass_file_with_path, remote_script_path) == 0:          
            
                lines = []  
                lines.append('Write-Host "Execute Remote Powershell Command with Mount Drive"\n')
                lines.append('[Byte[]] $key = (1..16)\n')
                lines.append(f'$encrypted = Get-Content {mount_pass_file_with_path} | ConvertTo-SecureString -Key $key\n')  
                lines.append('$credential = New-Object System.Management.Automation.PsCredential("'+self.server_info['DOMAIN']+'\\'+self.server_info['USERNAME']+'", $encrypted)\n')
                lines.append('New-PSDrive -name "'+ self.server_info['SOFTWARE_REPO_TARGET_PATH'].split(':')[0]+'" -PSProvider FileSystem -Root "'+ self.environment_provider.get_share_root_win_path()+'" -Persist -Credential $credential\n')
                if execution_location == '':
                    lines.append(f'Set-Location -Path {os.path.dirname(mount_pass_file_with_path)} \n')
                else:
                    lines.append(f'Set-Location -Path {execution_location} \n')
                for env_var in env_vars:                    
                    lines.append(f'$env:{env_var}="{env_vars[env_var]}"')
                lines.append(f'& {command_with_path} \n')
                content = '\n'.join(lines) + '\n'
                
                
                if remote_script_path == '':
                    remote_script_path = os.path.join(os.path.dirname(mount_pass_file_with_path),str(uuid.uuid4()).replace('-', '_')+'.ps1')
                    remote_script_path = remote_script_path.replace('/', '\\')
                
                _create_file = File(remote_script_path).remote_write_new_file(ssh_client, content)
                
                ssh_connection = ssh_client.connect()
                
                # Run the uploaded PowerShell script remotely
                stdin, stdout, stderr = ssh_connection.exec_command(f'powershell.exe -File {remote_script_path}')
                output_lines = []
                error_lines = []
                try:                    
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
                                    if 'return' in keyword.split('::')[1].lower():
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
                    for line in stderr:
                        error_lines.append(line.strip())
                        #self.log.error(f"{line.strip()}")
                except custom_exception:
                    raise  # Re-raise the custom exception
                except Exception as e:
                    self.log.error(e)
                    return stdout
                
                # Check the exit status
                exit_code = stdout.channel.recv_exit_status()
                
                ssh_connection.exec_command(f'del {remote_script_path}')
                
                ssh_client.close()                
                return exit_code, output_lines, error_lines
            
    def create_directory_if_not_exists(self, directory_path):
        self.update_host_info()
        if self.__is_windows:
            ssh_client = SSHConnection(self.server_info['USERNAME'],self.server_info['HOSTNAME']) # ssh connection established
            try:
                ssh_connection = ssh_client.connect()
                # Check if the directory exists, create if it doesn't
                command = f'if not exist "{directory_path}" mkdir "{directory_path}"'
                stdin, stdout, stderr = ssh_connection.exec_command(command)
                output_lines = []
                error_lines = []
                for line in stdout:
                    output_lines.append(line.strip())
                    self.log.debug(line.strip())
                for line in stderr:
                    error_lines.append(line.strip())
                    self.log.error(line.strip())
                # Check the exit status
                exit_code = stdout.channel.recv_exit_status()
                return exit_code, output_lines, error_lines
            except Exception as e:
                self.log.error(e)
                return 1
    
    def remote_check_file_exists(self, remote_path):

        self.update_host_info()
        
        if self.__is_windows:
            
            ssh_client = SSHConnection(self.server_info['USERNAME'],self.server_info['HOSTNAME']) # ssh connection established
            
            ssh_connection = ssh_client.connect()
            
            # Command to check if the file exists
            command = f'powershell.exe Test-Path "{remote_path}"'
            
            # Execute the command
            stdin, stdout, stderr = ssh_connection.exec_command(command)
            _result = 1
            for line in stdout:
                self.log.debug(f"{remote_path} - {line.strip()}")
                if line.strip() == 'True':
                    _result=0
            for line in stderr:
                self.log.error(line.strip())
                _result=1
                
            # Check the exit status
            exit_status = stdout.channel.recv_exit_status()                                                
            ssh_client.close()
            return _result
        else:
            ssh_client = SSHConnection(self.server_info['USERNAME'],self.server_info['HOSTNAME']) # ssh connection established           

            ssh_connection = ssh_client.connect()
            
            command = f'stat {remote_path}'  # Command to check file existence using stat
            stdin, stdout, stderr = ssh_connection.exec_command(command)
            if not stderr.read().decode('utf-8'):
                print(f"File '{remote_path}' exists.")
            else:
                print(f"File '{remote_path}' does not exist or there was an error.")
            return 0
            

            
            
    def extract_zip_to_file(self, zip_utility_path, zip_filename_with_path, output_path, extract_filename):
    
        if self.__is_windows:

            ssh_client = SSHConnection(self.server_info['USERNAME'],self.server_info['HOSTNAME']) # ssh connection established
        
            ssh_connection = ssh_client.connect()
            
            # Command to extract a specific file using 7-Zip
            command = f'{zip_utility_path} e {zip_filename_with_path} -o{output_path} {extract_filename} -r -y'
            
            self.log.debug(command)
            
            # Execute the command
            stdin, stdout, stderr = ssh_connection.exec_command(command)
            # Read output
            #output = stdout.read().decode('utf-8')
            #error = stderr.read().decode('utf-8')
            
            for line in stdout:
                self.log.debug(line.strip())
            for line in stderr:
                self.log.error(line.strip())
                
            # Check the exit status
            exit_status = stdout.channel.recv_exit_status()
            
            ssh_client.close()

            if exit_status == 0:
                self.log.info(f"Extract the {extract_filename} from {zip_filename_with_path} Successfully!")
                return exit_status
            else:
                self.log.error(f"Extract the {extract_filename} from {zip_filename_with_path} Failed!")
                return 1