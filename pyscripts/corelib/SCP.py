from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.File import BaseFile
from corelib.DateTime import DateTime
import os
import tempfile

class SCP(Loggable):

    def __init__(self, ssh_hostname = ''):  
        
        super().__init__(__name__)


        self.__ssh_hostname = ssh_hostname

        self.__timeout = 0

    def set_timeout(self, timeout: int):

        """
        Sets the timeout which should be user for the process
        Timeout in seconds
        """

        self.__timeout = timeout

    def copy_remote_to_remote(self, source, destination, _src_ssh, parallel = False):

        """
        Copy a remote file to a remote host
        """

        destination = BaseFile.get_obj_path(destination)
        source = BaseFile.get_obj_path(source)

        if _src_ssh != '':
            source = _src_ssh + ':' + source

        return self.__copy(source, self.build_remote_param(destination),parallel)

    def copy_from_remote(self, source, destination, parallel = False):

        """
        Copy a local file to a remote host
        """

        destination = BaseFile.get_obj_path(destination)
        source = BaseFile.get_obj_path(source)

        return self.__copy(self.build_remote_param(source), BaseFile.get_obj_path(destination),parallel)

    def copy_to_remote(self, source, destination, parallel = False):

        """
        Copy a local file to a remote host
        """

        destination = BaseFile.get_obj_path(destination)
        source = BaseFile.get_obj_path(source)

        return self.__copy(BaseFile.get_obj_path(source), self.build_remote_param(destination),parallel)

    def copy_to_local(self, source, destination, parallel = False):

        """
        Copy a remote file to the localhost
        """

        destination = BaseFile.get_obj_path(destination)
        source = BaseFile.get_obj_path(source)

        return self.__copy(self.build_remote_param(source), BaseFile.get_obj_path(destination),parallel)
    
    def copy(self, source, destination, parallel=False):
        """
        Copy a file or folder into same server
        """
        destination = BaseFile.get_obj_path(destination)
        source = BaseFile.get_obj_path(source)

        return self.__cp(source, destination, parallel)

    def copy_ssh(self, source, destination, parallel=False):
        """
        Copy a file or folder into same server
        """
        destination = BaseFile.get_obj_path(destination)
        source = BaseFile.get_obj_path(source)       

        return self.__cp__ssh(source, destination, parallel)
        
        
    def unzip(self, source, destination, parallel=False):
        """
        Unzip the file
        """
        source = BaseFile.get_obj_path(source)
        destination = BaseFile.get_obj_path(destination)
        args = []
        if self.__ssh_hostname:
            args.append(self.__ssh_hostname)   
        args.append('unzip')
        args.append(source)
        args.append('-d')
        args.append(destination)

        self.log.debug('Unzip from ' + source + ' to '+ destination)
        args = ' '.join([str(elem) for elem in args])
        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        result = process.execute() 
        return result
        
    def zip(self, source, destination, parallel=False):
        """
        Unzip the file
        """
        source = BaseFile.get_obj_path(source)
        destination = BaseFile.get_obj_path(destination)
        args = []
        if self.__ssh_hostname:
            args.append(self.__ssh_hostname)   
        args.append('tar -cvf')
        args.append(source)
        args.append('-C')
        args.append(destination)
        args.append('.')      

        self.log.debug('zip from ' + source + ' to '+ destination)

        args = ' '.join([str(elem) for elem in args])
        
        self.log.info(args)

        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        result = process.execute() 
        return result
        
    def copy_to_mount_win(self, SOURCE, DESTINATION, FILENAME, DRIVELETTER, ROOTPATH, MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH, DOMAIN, USERNAME, LOCATION, SERVER_INFO, parallel=False):
    
        lines = []
        lines.append(f'Write-Host "{FILENAME} Copy Started"')
        lines.append('[Byte[]] $key = (1..16)\n')
        lines.append(f'$encrypted = Get-Content {MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH} | ConvertTo-SecureString -Key $key')
        lines.append(f'$credential = New-Object System.Management.Automation.PsCredential("{DOMAIN}\\{USERNAME}", $encrypted)')
        lines.append(f'New-PSDrive -name "{DRIVELETTER}" -PSProvider FileSystem -Root "{ROOTPATH}" -Persist -Credential $credential')
        lines.append(f'Set-Location -Path {LOCATION}')
        lines.append(f'Remove-Item "{DESTINATION}/{FILENAME}" -Force') 
        lines.append(f'Start-Sleep -Seconds 15;')
        lines.append(f'ROBOCOPY "{SOURCE}" "{DESTINATION}" "{FILENAME}" /IS /NJS')
        file  = tempfile.NamedTemporaryFile('w+t')
        filepath = file.name
        for line in lines:
            self.log.debug(line)
            file.write(line + '\n')
        file.flush()
        _psfilename = f'copytomount{SERVER_INFO["ALIASNAME"]}{DateTime.get_datetime("%d%m%Y%H%M%S")}.ps1'
        self.copy_to_remote(filepath, os.path.join(SERVER_INFO['DEPLOYMENT_CENTER_TEMP_DIR'],_psfilename))
        args = ['ssh',self.__ssh_hostname]
        args.append('"cd '+SERVER_INFO['DEPLOYMENT_CENTER_TEMP_DIR']+' && '+SERVER_INFO['DEPLOYMENT_CENTER_TEMP_DIR'].split(':')[0]+':'+' && powershell '+SERVER_INFO['DEPLOYMENT_CENTER_TEMP_DIR']+'/'+_psfilename+'"')
        args = ' '.join([str(elem) for elem in args])
        process = Process(args)
        process.set_parallel_execution(parallel)
        #process.set_stderr(False)
        return process.execute()
        
        
    def unzip_to_mount_win(self, SOURCE, DESTINATION, FILENAME, DRIVELETTER, ROOTPATH, MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH, DOMAIN, USERNAME, LOCATION, SERVER_INFO, parallel=False):
    
        lines = []
        lines.append(f'Write-Host "{FILENAME} Copy Started"')
        lines.append('[Byte[]] $key = (1..16)\n')
        lines.append(f'$encrypted = Get-Content {MOUNT_DRIVE_ENCRYPTED_PASSWORD_PATH} | ConvertTo-SecureString -Key $key')
        lines.append(f'$credential = New-Object System.Management.Automation.PsCredential("{DOMAIN}\\{USERNAME}", $encrypted)')
        lines.append(f'New-PSDrive -name "{DRIVELETTER}" -PSProvider FileSystem -Root "{ROOTPATH}" -Persist -Credential $credential')
        lines.append(f'Set-Location -Path {LOCATION}')
        lines.append(f'Start-Sleep -Seconds 15;')
        
        lines.append(f'& "C:/Progra~1/7-Zip/7z.exe" x "{SOURCE}/{FILENAME}" -o"{DESTINATION}" -aoa ')
        lines.append(f'Remove-Item "{SOURCE}/{FILENAME}" -Force')
        file  = tempfile.NamedTemporaryFile('w+t')
        filepath = file.name
        for line in lines:
            self.log.debug(line)
            file.write(line + '\n')
        file.flush()
        _psfilename = f'copytomount{SERVER_INFO["ALIASNAME"]}{DateTime.get_datetime("%d%m%Y%H%M%S")}.ps1'
        self.copy_to_remote(filepath, os.path.join(SERVER_INFO['DEPLOYMENT_CENTER_TEMP_DIR'],_psfilename))
        args = ['ssh',self.__ssh_hostname]
        args.append('"cd '+SERVER_INFO['DEPLOYMENT_CENTER_TEMP_DIR']+' && '+SERVER_INFO['DEPLOYMENT_CENTER_TEMP_DIR'].split(':')[0]+':'+' && powershell '+SERVER_INFO['DEPLOYMENT_CENTER_TEMP_DIR']+'/'+_psfilename+'"')
        args = ' '.join([str(elem) for elem in args])
        self.log.info(args)
        process = Process(args)
        process.set_parallel_execution(parallel)
        process.set_stderr(False)
        return process.execute()
        
    def rsnyc_to_remote(self, source, destination, parallel = False):

        """
        Copy a local file to a remote host
        """

        destination = BaseFile.get_obj_path(destination)
        source = BaseFile.get_obj_path(source)

        return self.__rsnyc(BaseFile.get_obj_path(source), self.build_remote_param(destination),parallel)
    

    def rsnyc_to_local(self, source, destination, parallel = False, exclude = [], logfile= ''):

        """
        Copy a remote file to the localhost
        """

        destination = BaseFile.get_obj_path(destination)
        source = BaseFile.get_obj_path(source)

        return self.__rsnyc(self.build_remote_param(source), BaseFile.get_obj_path(destination),parallel, exclude, logfile)

    

    def __copy(self, source: str, dest: str, parallel):
        """
        Copy a file from source to dest with scp
        """
        args = ['scp', '-pr']

        args.append(source)
        args.append(dest)

        self.log.debug('Copying from ' + source + ' to ' + dest)

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        process.set_parallel_execution(parallel)
        return process.execute()
    
    def __cp(self, source: str, dest: str, parallel):

        """
        copy a file or folder from source to dest with cp
        """
        args = ['cp', '-r']
        args.append(source)
        args.append(dest)

        self.log.debug('Copying from ' + source + ' to '+ dest)

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        process.set_parallel_execution(parallel)
        return process.execute()
        
        
    def __cp__ssh(self, source: str, dest: str, parallel):

        """
        copy a file or folder from source to dest with cp
        """
        args = []
        if self.__ssh_hostname:
            args.append(self.__ssh_hostname)            
        args.append('cp')
        args.append('-r')
        args.append(source)
        args.append(dest)

        self.log.debug('Copying from ' + source + ' to '+ dest)
        
        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        process.set_parallel_execution(parallel)
        return process.execute()


    def build_remote_param(self, path: str):
        """
        Builds the remote parameter for scp
        """
        if self.__ssh_hostname == '':
            return path
        return  self.__ssh_hostname + ':' + path
    
    def __rsnyc(self, source: str, dest:str, parallel = False, excludes = [], logfile = ''):

        args = ["rsync", "-avt", "--progress", "--out-format='%t %b %n'"]
        if excludes:
            for entry in excludes:
                exclude_path = BaseFile.get_obj_path(entry)
                args.extend(["--exclude " + exclude_path])
        args.append(source)
        args.append(dest)
        if logfile:
            args.append('> '+ logfile)
        #     args.append('--log-file='+logfile)
        self.log.debug('Copying from ' + source + ' to ' + dest)

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        process.set_parallel_execution(parallel)
        return process.execute()

    def get_latest_folder_from_path(self, path, is_windows = False):           
        
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]

        if is_windows:
            args.append('"cd')    
            args.append(path)  
            args.append('&& '+ path.split(':')[0] +':')
            args.append('&& dir /b /OD"') 
        else:
            args.append('cd')    
            args.append(path)  
            args.append("&& ls -td -- */ | head -n 1 | cut -d'/' -f1") 
        
        args = ' '.join([str(elem) for elem in args])
        
        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        result = process.execute()        
        
        listoffoldernames = process.get_out_lines()
        
        dcpath = os.path.join(path, listoffoldernames[len(listoffoldernames) - 1])
        self.log.debug('Get DeployScript path: ' + dcpath)
        
        return listoffoldernames[len(listoffoldernames) - 1] 


    def get_latest_file_from_path(self, path, temp_dir, extension=None, is_windows=False, ):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]

        if is_windows:
            file  = tempfile.NamedTemporaryFile('w+t')
            filepath = file.name
            command = f'Get-ChildItem -Path {path} -File | sort LastWriteTime | select -last 1 | Format-Wide -Property Name'
            if extension:
                command = f'Get-ChildItem -Path {path} -Filter "*.{extension}" -File | sort LastWriteTime | select -last 1 | Format-Wide -Property Name'
            self.log.debug(command)
            file.write(command + '\n')
            file.flush()

            result = SCP(self.__ssh_hostname.split()[-1]).copy_to_remote(filepath, os.path.join(temp_dir, 'getlatestfilefrompath.ps1'))
            if result == 0:
                args.append('"cd ' + temp_dir + ' && ' + temp_dir.split(':')[0] + ':' + ' && powershell '+ temp_dir + '/getlatestfilefrompath.ps1"')
            else:
                return 1
        else:
            args.append('cd')
            args.append(path)
            command = f"&& ls -Art | tail -n 1"
            if extension:
                command = f"&& ls -Art -- *.{extension}| tail -n 1"
            args.append(command)

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        result = process.execute()

        final_file = [line.strip() for line in process.get_out_lines() if line]
        if len(final_file):
            self.log.debug(f'latest file: {final_file[0]}')
            return final_file[0]
        return ''
    
    
    def check_empty_dir_from_remote(self, is_windows, path, temp_dir, level=0, recurse=True, check_files_only=False):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]
        if self.check_dir_to_remote(is_windows, path):
            if is_windows:
                file = tempfile.NamedTemporaryFile('w+t')
                filepath = file.name
                command = f'Get-ChildItem {path} -Depth {level}'
                if recurse:
                    command = f'Get-ChildItem {path} -Recurse'
                if check_files_only:
                    command = command + ' -File'
                self.log.debug(command)
                file.write(command + '\n')
                file.flush()
                result = SCP(self.__ssh_hostname.split()[-1]).copy_to_remote(filepath, os.path.join(temp_dir,'checkemptydirtoremote.ps1'))
                if result == 0:
                    args.append('"cd '+temp_dir+' && '+temp_dir.split(':')[0]+':'+' && powershell '+temp_dir+'/checkemptydirtoremote.ps1"')
                else:
                    return 1
            else:
                level += 1
                command = f"find {path} -maxdepth {level}"
                if recurse:
                    command = f"find {path}"
                if check_files_only:
                    command = command + ' -type f'
                self.log.debug(command)
                args.append(command)

            args = ' '.join([str(elem) for elem in args])

            process = Process(args)
            process.hide_output()
            process.collect_output()
            process.ignore_errors()
            process.execute()
            output_result = [res for res in process.get_out_lines() if res != '']

            if len(output_result):
                return False
            return True

        self.log.warning(f'{path} Does not Exists...')
        return True
    
    def get_filtered_files_from_remote(self, path, is_windows, temp_dir, filter='*'):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]
        if self.check_dir_to_remote(is_windows, path):
            if is_windows:
                file  = tempfile.NamedTemporaryFile('w+t')
                filepath = file.name
                command = f'Get-ChildItem -Path {path} -Filter "{filter}" -File -Name'
                self.log.debug(command)
                file.write(command + '\n')
                file.flush()
                result = SCP(self.__ssh_hostname.split()[-1]).copy_to_remote(filepath, os.path.join(temp_dir, 'getfilteredfilesfromremote.ps1'))
                if result == 0:
                    args.append('"cd ' + temp_dir + ' && ' + temp_dir.split(':')[0] + ':' + ' && powershell '+ temp_dir + '/getfilteredfilesfromremote.ps1"')
                else:
                    self.log.warning('Falied copying "getfilteredfilesfromremote.ps1" to remote server.')
                    return []
            else:
                args.append('cd')
                args.append(path)
                command = f"&& ls -Art1 -- {filter} 2> /dev/null || true"
                args.append(command)

            args = ' '.join([str(elem) for elem in args])

            process = Process(args)
            process.hide_output()
            process.collect_output()
            process.ignore_errors()
            result = process.execute()

            files = [line.strip() for line in process.get_out_lines() if line]
            if len(files):
                return files
            return []

        self.log.warning(f'{path} Does not Exists...')
        return []

      
    
    def check_dir_to_remote(self, is_windows, path):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]
        if is_windows:
            args.append('if exist')
            args.append(path)
            args.append('echo yes')
        else:
            args.append(f'test -e "{path}" && echo "yes" || echo "no"')
        args = ' '.join([str(elem) for elem in args]) 
        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        process.execute()
        if len(process.get_out_lines()):
            if 'yes' in process.get_out_lines():
                return True
            else:
                return False
        else:
            return False
        
    def remove_multiple_files_to_remote(self,is_windows,file_list,temp_dir = ''):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]

        file  = tempfile.NamedTemporaryFile('w+t')
        filepath = file.name
        for line_data in file_list:
            if is_windows:
                line = f'Remove-Item -Path "{line_data}" -Recurse -Force -ErrorAction SilentlyContinue -ErrorVariable +Errors;if ($Errors) {{ Write-Host {line_data} }}'
            else:
                line = line_data
            self.log.debug(line)
            file.write(line + '\n')
        file.flush()
        if is_windows:
            result = SCP(self.__ssh_hostname.split()[-1]).copy_to_remote(filepath, os.path.join(temp_dir,'removetempfilesbythreshold.ps1'))
            if result == 0:
                args.append('"cd '+temp_dir+' && '+temp_dir.split(':')[0]+':'+' && powershell '+temp_dir+'/removetempfilesbythreshold.ps1"')
            else:
                return 1
        else:
            temp_file_name = os.path.join(temp_dir,'removetempfilesbythreshold')
            if len(self.__ssh_hostname):
                result = SCP(self.__ssh_hostname.split()[-1]).copy_to_remote(filepath, temp_file_name)
            else:
                result = SCP('').copy_to_local(filepath, temp_file_name)
            if result == 0:
                args.extend(["xargs", "-a", temp_file_name, "rm", "-rf",])
            else:
                return 1

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        process.execute()
        output_result = [res for res in process.get_out_lines() if res != '']
        if len(output_result):
            for undeleted_path in output_result:
                self.log.warning(f'{undeleted_path} is Not deleted...! May be the file or Directory is in Use')
        return 0
 
    
    def remove_file_to_remote(self, is_windows, path , is_path = False):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]
        
        if is_windows:
            if is_path:
                args.append('rmdir /s /q')
            else:
                args.append('Del /q')
            path = path.replace('/','\\')
            args.append(f'"{path}"')
        else:
            if len(self.__ssh_hostname):
                args.append(f'rm -rf "{path}"')
            else:
                args.append(f'rm -rf {path}')
        args = ' '.join([str(elem) for elem in args])
        process = Process(args)
        return process.execute()

    def create_dir_to_remote(self,is_windows,path):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]
        if is_windows:
            path = path.replace('/',r'\\')
            args.append(f'"mkdir {path} 2>NUL || echo."')
        else:
            args.append(f"mkdir -p {path}" )  

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        return process.execute()
    

    def create_dir_to_local(self,is_windows,path):
        args = []        
        if is_windows:
            path = path.replace('/',r'\\')
            args.append(f'"mkdir {path} 2>NUL || echo."')
        else:
            args.append(f"mkdir -p {path}" )  

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        return process.execute()
                                                                                                     

    def rename_dir_to_remote(self,is_windows, path,new_name):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]
        if is_windows:
            path = path.replace('/',r'\\')
            new_name = new_name.split(r'/')[-1]
            args.append(f'ren "{path}" "{new_name}"')
        else:
            args.append(f'mv -v {path} {new_name}') 

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        return process.execute()
    
    def rename_file_to_remote(self,is_windows,file_path):
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]

        if is_windows:
            file_name = file_path.split('/')[-1]
            new_name = file_name.split('.')[0]+'_'+ DateTime.get_datetime("%d%m%Y%H%M%S")+'.'+file_name.split('.')[-1]
            file_path = file_path.replace('/',r'\\')

            args.append(f'ren "{file_path}" "{new_name}"')
        else:
            new_name = file_path.split('.')[0]+'_'+DateTime.get_datetime("%d%m%Y%H%M%S")

            args.append(f'mv -v {file_path} {new_name}') 

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        return process.execute()

    def get_files_from_remote(self,path,is_windows, files_only = False,threshhold = False):
        
        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]
        if '*' in path:
            abs_path = os.path.dirname(path)
        else:
            abs_path = path
        if self.check_dir_to_remote(is_windows,abs_path):
            if bool(threshhold):
                _split_path = path.rsplit('/',1)
                if is_windows:
                    log_root_dir=_split_path[0].replace('/','\\')
                    args.extend(["'forfiles /p",f'"{log_root_dir}"',f'/m "{_split_path[-1]}"',f'/d -{threshhold} /c','"cmd /c echo @path" 2>$null || echo ""',"'"])
                else:
                    if len(self.__ssh_hostname):
                        args.extend(["'find",_split_path[0] ,'-mindepth 1 -maxdepth 1 -name',f'"{_split_path[1]}"',f"-mtime +{threshhold}'"])
                    else:
                        args.extend(["find",_split_path[0] ,'-mindepth 1 -maxdepth 1 -name',f'"{_split_path[1]}"',f"-mtime +{threshhold}"])           
            else:
                if  is_windows:  
                    if files_only:
                        args.append(f'dir /A-D /B \\"{path}\\"')
                    else:
                        args.append(f'dir /a /b \\"{path}\\"')
                else:
                    if files_only:
                        args.append(f'ls -p {path} | grep -v /')
                    else:
                        args.append(f'ls -A {path}')

            args = ' '.join([str(elem) for elem in args])

            process = Process(args)
            process.collect_output()
            process.execute()
            if bool(threshhold):
                result = [files.replace('"','') for files in process.get_out_lines() if files != '']
                return [file for file in result if file.strip() != '']
            
            if files_only:
                self.log.info(f'Collecting all files from {path}')
            else:
                self.log.info(f'Collecting All files and folders from {path}')
                
            list_of_files = [item for item in process.get_out_lines()]

            return list_of_files
        
        else:
            self.log.warning(f'{path} Does not Exists...')
            return []


    def chmod_remote(self, path, is_windows, permission = '0777'):

        if self.__ssh_hostname == '':
            args = []
        else:
            args = [self.__ssh_hostname]
        if is_windows:
            self.log.debug('Windows No Need CHMOD Permission')
            return 0
        else:
            args.append(f'chmod -R {permission} {path}') 

        args = ' '.join([str(elem) for elem in args])

        process = Process(args)
        return process.execute()

    def read_file_from_remote(self, remote_path, is_windows):

        if self.__ssh_hostname =='':
            command=[]
        else:
            command=[self.__ssh_hostname]
        if is_windows:
            remote_path = remote_path.replace('/','\\')
            seperate_path= remote_path.rsplit('\\',1)
            command.append(f'"cd {seperate_path[0]} && type {seperate_path[-1]}"')
        else:
            command.append(f'cat {remote_path}')
            
        args = ' '.join([str(elem) for elem in command])
        process = Process(args)
        process.hide_output()
        process.collect_output()
        process.ignore_errors()
        process.execute()
        output_result = [res for res in process.get_out_lines() if res != '']

        if len(output_result):
            return '\n'.join(output_result)
        else:
            self.log.warning(f"file is empty")
            return ''
        
        