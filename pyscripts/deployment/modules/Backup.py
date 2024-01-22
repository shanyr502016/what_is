"""
Backup deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
import os
from corelib.BackupUtilities import BackupUtilities
from corelib.DateTime import DateTime
from corelib.SCP import SCP


class Backup(Loggable):
    
    def __init__(self, args):   

        super().__init__(__name__)
        
        """
        Set arguments from DynamicImporter
        """         
        self.__arguments = args
        
        """
        Get the Environment Specific Values from config json
        """        
        self.__environment = args._environment
        """
        Get the Module Specific Values from config json
        """        
        self.__properties = args._properties
        """
        Get the Environment Provider method
        Reusable method derived
        """        
        self.__environment_provider = args._environment_provider
        """
        Module name from user commandline (Only Module (classname))
        """       
        self.__module_name = args._module_name
        """
        Sub Module name from user commandline (Only Sub Module (classname))
        """
        self.__sub_module_name = args._sub_module_name

        """
        Target Teamcenter Package ID get from user commandline
        """        
        self._tcpackage_id = args._tcpackage_id

        """
        Target Instances setup
        """        
        self.__target = None

        self.__action = None

        """
        Remote Execution.
        """
        self.__remote_execution = False        
        """
        Target Environment Type if linux
        """
        self.__is_linux = False
        
        """
        Target Environment Type if windows
        """        
        self.__is_windows = False

        """
        Resume State Skip
        """
        self._resumestate = args._arguments.resumestate
        
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
            
        self._backupUtilities = BackupUtilities(self.__environment_provider)
        
        self._processes = []
        self._parallel = False
        self._overallbackup = False
        self._processesLabel = []

    
    def default(self):
                
        self.log.info("Backup All")
        self._parallel = True
        self._overallbackup = True
        self._executeTargets()   
        self._execute_process()

    def rmsharedmemdir(self):

        self.log.info("Rename Shared Memory Directory ")

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 

        _timestamp = DateTime.get_datetime("%d%m%Y")

        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Renaming the Shared Memory Directory {self.__properties[self.__target]['logFolderPath']} - [{server_info['HOSTNAME']}]")

            _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])
            
            _ssh_command = self.__environment_provider.get_ssh_command(server_info)
            
            _target_path = self.__properties[self.__target]['logFolderPath']

            _rename_path = _target_path + '_OLD_'+ _timestamp

            _renameFolderResult = SCP(_ssh_command).rename_dir_to_remote(_is_windows,_target_path, _rename_path)

            self.__console_msg(_renameFolderResult,f'Renamed {_target_path} into {_rename_path}')



    def web(self):
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])    
        
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Starting WEB Backup {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]")

            _excludes = None

            if "excludes" in self.__properties[self.__target]:
                _excludes = self.__properties[self.__target]['excludes']
            
            _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

            if 'WEB_PATH' in server_info and (server_info['WEB_PATH'] and server_info['WEB_PATH'].strip()):

                sourcedir = server_info['WEB_PATH']
        
                self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['WEB_PATH']} - WEB Backup ", self.__target, _excludes)
            else:
                self.log.warning('WEB Backup Directory is not present in environment configuration! Backup Skipped.') 

    def warcreationsetup(self):

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])    
        
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Starting WEBSETUP Backup {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]")

            _excludes = None

            if "excludes" in self.__properties[self.__target]:
                _excludes = self.__properties[self.__target]['excludes']
            
            _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

            if 'WEBSETUP_PATH' in server_info and (server_info['WEBSETUP_PATH'] and server_info['WEBSETUP_PATH'].strip()):

                sourcedir = server_info['WEBSETUP_PATH']
        
                self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['WEBSETUP_PATH']} - WEBSETUP Backup ", self.__target, _excludes)
            else:
                self.log.warning('WEBSETUP Backup Directory is not present in environment configuration! Backup Skipped.') 



    def tcdata(self):        
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])    
        
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Starting TC_DATA Backup {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]")

            _excludes = None

            if "excludes" in self.__properties[self.__target]:
                _excludes = self.__properties[self.__target]['excludes']
            
            _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

            if 'TC_DATA' in server_info and (server_info['TC_DATA'] and server_info['TC_DATA'].strip()):

                sourcedir = server_info['TC_DATA']
        
                self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['TC_DATA']} - TC_DATA Backup",self.__target, _excludes)
            else:
                self.log.warning('TC_DATA Backup Directory is not present in environment configuration! Backup Skipped.')

   
    def tcprofilevars(self):        
        
        if 'parallel' in self.__properties[self.__target]:
            self._parallel = self.__properties[self.__target]['parallel']  

        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])    

        for index, server_info in enumerate(_execute_servers):

            _is_windows = self.__environment_provider.is_windows(server_info['OS_TYPE'])

            _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

            _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info,True))

            self.log.info(f"Starting TC_Profilevars Backup {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]")

            _excludes = None
            if "excludes" in self.__properties[self.__target]:
                _excludes = self.__properties[self.__target]['excludes']
        
            _sourcePath = os.path.join(server_info['SYNCTCDATA_PATH'],server_info['SMO_SHARE_TC_PROFILEVARS_NAME'])
            
            _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

            if not os.path.exists(_target_path):
                os.makedirs(_target_path)
    
            _check_exist = _scp_with_ssh.check_dir_to_remote(_is_windows,_sourcePath)

            if _check_exist:
            
                self.log.info(f'TC_Profilevars Location: {_sourcePath}')

                _copytoresult = _scp_without_ssh.copy_from_remote(_sourcePath,_target_path, self._parallel)
                
                self._processes.append({'NODE':server_info['NODE'],'process':_copytoresult,'module':self.__target, 'label': 'Backup TC_Profilevars'})
                self._processesLabel.append('TC_Profilevars Backup')
                if not self._parallel:
                    self.__console_msg( _copytoresult, 'TC_Profilevars Backup')
            else:
                self.log.warning('TC_Profilevars Backup File is not present in environment configuration! Backup Skipped.')
    
    def tcroot(self):

        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else:                
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])        
            
            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting TC_ROOT Backup {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]")
                
                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

                if 'TC_ROOT' in server_info and (server_info['TC_ROOT'] and server_info['TC_ROOT'].strip()):

                    sourcedir = server_info['TC_ROOT']
            
                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['TC_ROOT']} - TC_ROOT Backup", self.__target, _excludes)
                else:
                    self.log.warning('TC_ROOT Backup Directory is not present in environment configuration! Backup Skipped.')

            
    def volumes_dba(self):        
                
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else:  
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting Volumes DBA Backup {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]")

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

                if 'VOLUMES_DBA' in server_info and (server_info['VOLUMES_DBA'] and server_info['VOLUMES_DBA'].strip()): 

                    sourcedir = server_info['VOLUMES_DBA']
            
                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['VOLUMES_DBA']} - VOLUMES_DBA Backup", self.__target, _excludes)
                else:
                    self.log.warning('Volumes DBA Backup Directory is not present in environment configuration! Backup Skipped.')

            
    def volumes_all(self):        
                
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])    

        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Starting Volumes All Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]")       

            _excludes = None

            if "excludes" in self.__properties[self.__target]:
                _excludes = self.__properties[self.__target]['excludes']
            
            _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

            if 'VOLUMES' in server_info and (server_info['VOLUMES'] and server_info['VOLUMES'].strip()): 
                sourcedir = server_info['VOLUMES']
           
                self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info,  f"{server_info['HOSTNAME']} - {server_info['VOLUMES']} - VOLUMES Backup", self.__target, _excludes)
            else:
                self.log.warning('Volumes All Backup Directory is not present in environment configuration! Backup Skipped.')

            
    def deploymentcenter(self):

        if self.__target in self.__properties:
                
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 

            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting Deployment Center Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

                if 'DEPLOYMENT_CENTER_PATH' in server_info and (server_info['DEPLOYMENT_CENTER_PATH'] and server_info['DEPLOYMENT_CENTER_PATH'].strip()):     
                    
                    sourcedir = server_info['DEPLOYMENT_CENTER_PATH']
            
                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info,  f"{server_info['HOSTNAME']} - {server_info['DEPLOYMENT_CENTER_PATH']} - Deployment Center Backup",self.__target, _excludes)
                else:
                    self.log.warning('Deployment Center Backup Directory is not present in environment configuration! Backup Skipped.')               
        else:
            self.log.error('Check the Deployment Center Backup Command!')


    def dc(self):

        if self.__target in self.__properties:
                
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer']) 

            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting Deployment Center Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

                if 'DEPLOYMENT_CENTER_DC_PATH' in server_info and (server_info['DEPLOYMENT_CENTER_DC_PATH'] and server_info['DEPLOYMENT_CENTER_DC_PATH'].strip()):

                    sourcedir = server_info['DEPLOYMENT_CENTER_DC_PATH']

                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['DEPLOYMENT_CENTER_DC_PATH']} - Deployment Center DC Backup", self.__target, _excludes)  
                else:
                    self.log.warning('DC Backup Directory is not present in environment configuration! Backup Skipped.')               
        else:
            self.log.error('Check the DC Backup Command!')

    def dispatcherdata(self):                
        
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])       
            
            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting Dispatcher Backup Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME']) 

                if 'DISPATCHER_DATA_PATH' in server_info and (server_info['DISPATCHER_DATA_PATH'] and server_info['DISPATCHER_DATA_PATH'].strip()):                   

                    sourcedir = server_info['DISPATCHER_DATA_PATH']
            
                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['DISPATCHER_DATA_PATH']} - DISPATCHER DATA Backup", self.__target, _excludes)
                else:
                    self.log.warning('DISPATCHER_DATA Backup Directory is not present in environment configuration! Backup Skipped.')

    def dispatcher(self):

        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else:                
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])       
            
            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting Dispatcher Backup Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME']) 

                if 'DISPATCHER_PATH' in server_info and (server_info['DISPATCHER_PATH'] and server_info['DISPATCHER_PATH'].strip()):                   

                    sourcedir = server_info['DISPATCHER_PATH']
            
                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['DISPATCHER_PATH']} - DISPATCHER Backup", self.__target, _excludes)
                else:
                    self.log.warning('DISPATCHER Backup Directory is not present in environment configuration! Backup Skipped.')


    def dispatcherroot(self):
                
        
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])       
            
            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting Dispatcher Root Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])    

                if 'DISPATCHER_ROOT_PATH' in server_info and (server_info['DISPATCHER_ROOT_PATH'] and server_info['DISPATCHER_ROOT_PATH'].strip()):        

                    sourcedir = server_info['DISPATCHER_ROOT_PATH']
            
                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['DISPATCHER_ROOT_PATH']} - DISPATCHER ROOT Backup", self.__target, _excludes)
                else:
                    self.log.warning('Dispatcher_Root Backup Directory is not present in environment configuration! Backup Skipped.')


    def awc(self):

        if 'parallel' in self.__properties[self.__target]:
            
            self._parallel = self.__properties[self.__target]['parallel']
        
        if 'executeTargets' in self.__properties[self.__target]:
            
            self._executeCombineTargets()
        
        else: 
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting AWC Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']

                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

                if 'TC_ROOT' in server_info and (server_info['TC_ROOT'] and server_info['TC_ROOT'].strip()):

                    sourcedir = server_info['TC_ROOT']

                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['TC_ROOT']} - AWC Backup", self.__target, _excludes)
                else:
                    self.log.warning('AWC Backup Directory is not present in environment configuration! Backup Skipped.')

            if self._parallel and not self._overallbackup:
                self.log.info("Please wait while taking 10 to 15 minutes...") 
                output = [p['process'].wait() for p in self._processes]  
                for resultindex, result in enumerate(output):
                    self.__console_msg(result, self._processesLabel[resultindex])

    def adminData(self):
        '''
        command = admin_data_export -u=***-p=*** -g=dba -adminDataTypes=Organization -outputPackage=
        '''
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        for index, server_info in enumerate(_execute_servers):
            try:
                if 'command' in self.__properties[self.__target]:
                    _command = self.__properties[self.__target]['command']
                    __ssh_command = self.__environment_provider.get_ssh_command(server_info)
                    _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])
                    if __ssh_command == '':
                        args = []
                    else:
                        args = [__ssh_command]
                    args.extend([_command])
                    args.extend(['-u=' + server_info['TC_USER']])
                    args.extend(['-pf=' + server_info['TC_PWF'] ])
                    args.extend(['-g=' + server_info['TC_GROUP']])
                    args.extend(['-adminDataTypes=Organization'])
                    args.extend(['-outputPackage=' +os.path.join(_target_path,'adminData.zip')])
                    args = ' '.join([str(elem) for elem in args])
                    if self._parallel:
                        result = self._execute(args, _target_path)
                        self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': 'Admin Data Export'})
                        self._processesLabel.append('Admin Data Export')
                    else:
                        self.log.info("Please wait while taking few minutes...")
                        result = self._execute(args, _target_path)
                        self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': 'Admin Data Export'})
                        self.__console_msg(result, 'Admin Data Export') 
                else:
                    self.log.warning(f"Command is not present in Properties configuration! AdminData Backup Skipped.")              

            except Exception as exp:

                self.log.error(exp)
            
            
    def T4S(self):

        if 'parallel' in self.__properties[self.__target]:
            
            self._parallel = self.__properties[self.__target]['parallel']
                
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])         
            
            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting T4S Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

                if 'T4S' in server_info and (server_info['T4S'] and server_info['T4S'].strip()):

                    sourcedir = server_info['T4S']
            
                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['T4S']} - T4S Backup", self.__target, _excludes)
                else:
                    self.log.warning('T4S Backup Directory is not present in environment configuration! Backup Skipped.')
            if self._parallel and not self._overallbackup:
                self.log.info("Please wait while taking 10 to 15 minutes...") 
                output = [_process['process'].wait() for _process in self._processes]
                for resultindex, result in enumerate(output):
                    self.__console_msg(result, self._processesLabel[resultindex])
            
            
    def SSO_WebTier(self):
                
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])       
        
        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Starting SSO_WEBTIER Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

            _excludes = None

            if "excludes" in self.__properties[self.__target]:
                _excludes = self.__properties[self.__target]['excludes']
            
            _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

            if 'SSO_WEBTIER' in server_info and (server_info['SSO_WEBTIER'] and server_info['SSO_WEBTIER'].strip()):

                sourcedir = server_info['SSO_WEBTIER']
           
                self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info, f"{server_info['HOSTNAME']} - {server_info['SSO_WEBTIER']} - SSO_WEBTIER Backup", self.__target, _excludes)
            else:
                self.log.warning('SSO_WEBTIER Backup Directory is not present in environment configuration! Backup Skipped.')

            
    def cpm(self):                
        
        if 'executeTargets' in self.__properties[self.__target]:
            self._executeCombineTargets()
        else: 
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])       
            
            for index, server_info in enumerate(_execute_servers):

                self.log.info(f"Starting CPM Backup from {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]") 

                _excludes = None

                if "excludes" in self.__properties[self.__target]:
                    _excludes = self.__properties[self.__target]['excludes']
                
                _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME'])

                if 'CPM' in server_info and (server_info['CPM'] and server_info['CPM'].strip()):

                    sourcedir = server_info['CPM']
            
                    self._build_arguments(sourcedir, os.path.basename(sourcedir), _target_path, server_info,  f"{server_info['HOSTNAME']} - {server_info['CPM']} - CPM Backup", self.__target, _excludes)
                else:
                    self.log.warning('CPM Backup Directory is not present in environment configuration! Backup Skipped.')


    def infodba(self):

        self._parallel = False
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])  

        for index, server_info in enumerate(_execute_servers):

            __ssh_command = self.__environment_provider.get_ssh_command(server_info)
            

            _LD_LIBRARY_PATH = server_info['LD_LIBRARY_PATH']
            _BASHRC = server_info['BASHRC']
            _ORACLE_HOME = server_info['ORACLE_HOME']
            _DB_USERNAME = server_info['DB_USERNAME']
            _DB_PASSWORD = server_info['DB_PASSWORD']
            _DB_SSID = server_info['DB_SSID']
            _DB_DIRECTORY = server_info['DB_DIRECTORY']

            _SCHEMAS = server_info['SCHEMAS']

            args_expdp = []

            if __ssh_command == '':
                args_expdp.append('export LD_LIBRARY_PATH='+ _LD_LIBRARY_PATH+':$LD_LIBRARY_PATH') 
                args_expdp.append('&&') 
                args_expdp.append('export PATH=$LD_LIBRARY_PATH:$PATH') 
                args_expdp.append('&&')  
                args_expdp.append(_BASHRC)  
                args_expdp.append('&&')  
                args_expdp.append('export ORACLE_HOME='+ _ORACLE_HOME + '/') 
                args_expdp.append('&&')         
                args_expdp.append('cd '+_ORACLE_HOME+'/bin &&') 
                args_expdp.append('expdp')              
            else:
                args_expdp.append('cd '+_ORACLE_HOME+'/bin &&')
                args_expdp.append('expdp')
            args_expdp.append("'"+_DB_USERNAME+'/"'+_DB_PASSWORD+'"@'+_DB_SSID+"'")

            args_expdp.append('directory='+_DB_DIRECTORY)
            args_expdp.append('dumpfile='+self._tcpackage_id + '_infodba' + '.dmp')
            args_expdp.append('logfile='+self._tcpackage_id + '_infodba' + '.log')
            args_expdp.append("schemas='"+_SCHEMAS+"'")

            args_expdp = ' '.join([str(elem) for elem in args_expdp])
            

            if self._parallel:
                self.log.info("Please wait while taking 10 to 15 minutes...")
                result = self._execute(args_expdp, _ORACLE_HOME+'/bin', False)
                #self._processes.append(result)
                self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': 'Backup infodba'})
                self._processesLabel.append('Backup infodba')
            else:
                self.log.info("Please wait while taking 10 to 15 minutes...")
                result = self._execute(args_expdp, _ORACLE_HOME+'/bin', False)
                self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': 'Backup infodba'})
                self.__console_msg(result, 'Backup infodba')

  

    def pooldb(self):
            
            self._parallel = False
            
            _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])  

            for index, server_info in enumerate(_execute_servers):

                __ssh_command = self.__environment_provider.get_ssh_command(server_info)
                

                _LD_LIBRARY_PATH = server_info['LD_LIBRARY_PATH']
                _BASHRC = server_info['BASHRC']
                _ORACLE_HOME = server_info['ORACLE_HOME']
                _DB_USERNAME = server_info['POOL_DB_USERNAME']
                _DB_PASSWORD = server_info['POOL_DB_PASSWORD']
                _DB_SSID = server_info['POOL_DB_SSID']
                _DB_DIRECTORY = server_info['POOL_DB_DIRECTORY']

                _SCHEMAS = server_info['POOL_SCHEMAS']

                args_expdp = []
                if __ssh_command == '':
                    args_expdp.append('export LD_LIBRARY_PATH='+ _LD_LIBRARY_PATH+':$LD_LIBRARY_PATH') 
                    args_expdp.append('&&') 
                    args_expdp.append('export PATH=$LD_LIBRARY_PATH:$PATH') 
                    args_expdp.append('&&')  
                    args_expdp.append(_BASHRC)  
                    args_expdp.append('&&')  
                    args_expdp.append('export ORACLE_HOME='+ _ORACLE_HOME + '/') 
                    args_expdp.append('&&')         
                    args_expdp.append('cd '+_ORACLE_HOME+'/bin &&') 
                    args_expdp.append('expdp')              
                else:
                    args_expdp.append('cd '+_ORACLE_HOME+'/bin &&')
                    args_expdp.append('expdp')
                args_expdp.append("'"+_DB_USERNAME+'/"'+_DB_PASSWORD+'"@'+_DB_SSID+"'")

                args_expdp.append('directory='+_DB_DIRECTORY)
                args_expdp.append('dumpfile='+self._tcpackage_id + '_clusterIF' + '.dmp')
                args_expdp.append('logfile='+self._tcpackage_id + '_DEVDBADMIN' + '.log')
                args_expdp.append("schemas='"+_SCHEMAS+"'")

                args_expdp = ' '.join([str(elem) for elem in args_expdp])

                if self._parallel:
                    self.log.info("Please wait while taking 10 to 15 minutes...")
                    result = self._execute(args_expdp, _ORACLE_HOME+'/bin', False)
                    #self._processes.append(result)
                    self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': 'Backup Pool DB'})
                    self._processesLabel.append('Backup Pool DB')
                else:
                    self.log.info("Please wait while taking 10 to 15 minutes...")
                    result = self._execute(args_expdp, _ORACLE_HOME+'/bin', False)
                    self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': 'Backup Pool DB'})
                    self.__console_msg(result, 'Backup Pool DB')

    def Preferences(self): 
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

        _command = self.__properties[self.__target]['command']

        _scope = self.__properties[self.__target]['scope']

        for index, server_info in enumerate(_execute_servers):

            self.log.info(f"Starting Preferences Export {self.__properties[self.__target]['executionServer']} [{server_info['HOSTNAME']}]")

            _target_path = self.__environment_provider.get_backup_location(self.__properties[self.__target]['targetPath'], self._tcpackage_id, server_info['HOSTNAME']) 
            __ssh_command = self.__environment_provider.get_ssh_command(server_info)
            self._backupUtilities.set_backup_dest(_target_path, server_info)
            args = []
            if __ssh_command == '':
                args.append(_command)
            else:
                args.append(__ssh_command)
                args.append(_command)
            args.extend(['-u=' + server_info['TC_USER']])
            args.extend(['-g=' + server_info['TC_GROUP']])
            args.extend(['-pf=' + server_info['TC_PWF'] ])
            args.extend(['-scope='+ _scope])
            args.extend(['-mode=export'])
            args.extend(['-out_file='+ _target_path + '/preferences_' + _scope + '_' + DateTime.get_filename_timestamp() +'.xml' ])
            args = ' '.join([str(elem) for elem in args])
            if self._parallel:
                result = self._execute(args, _target_path)
                self._processes.append({'NODE':server_info['NODE'],'process':result,'module':self.__target, 'label': f"Preference Export"})
                self._processesLabel.append('Preference Export')
            else:
                self.log.info("Please wait while taking few minutes...")
                result = self._execute(args, _target_path)
                self.__console_msg(result, 'Preference Export')

    def _getServerNameByAlias(self,aliasname):
        for servername, properties in self.__environment.items():            
            if servername != 'ENVIRONMENT':                
                for values in properties:
                    if 'ALIASNAME' in values:                       
                        if values['ALIASNAME'].__ne__('') and values['ALIASNAME'].split('.')[0] == aliasname:
                            self.log.info(servername)
                            return servername

    def infra(self):            
        
        for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
            try:

                location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])

                env_path = os.path.join(location_in_package,self.__environment_provider.get_environment_name().lower())

                timestamp_path = DateTime.get_datetime("%d%m%Y%H%M%S")

                if os.path.exists(env_path): 

                    for alias_path in os.listdir(env_path):

                        alias_source_dir = os.path.join(env_path,alias_path)

                        for alias_src in os.listdir(alias_source_dir):

                            alias_src_dir = os.path.join(env_path,alias_path,alias_src)
                            
                            alias_path_files = [os.path.join(root, file).split(alias_source_dir)[-1] for root, dirs, files in os.walk(alias_src_dir) for file in files]

                            if len(alias_path_files):

                                executionServer = self._getServerNameByAlias(alias_path)

                                if executionServer:

                                    _execute_servers = self.__environment_provider.get_execute_server_details(executionServer)

                                    for index, server_info in enumerate(_execute_servers):

                                        _scp_with_ssh = SCP(self.__environment_provider.get_ssh_command(server_info))

                                        _scp_without_ssh = SCP(self.__environment_provider.get_ssh_command(server_info,True))

                                        _target_path = os.path.join(self.__environment_provider.get_share_root_path(),self.__properties[self.__target]['targetPath'])

                                        self.log.info(f'{alias_path} Backup Started')

                                        if self.__environment_provider.is_linux(server_info['OS_TYPE']):

                                            root_dir  = ''

                                            _temp_backup_path = os.path.join(_target_path,self.__environment_provider.get_environment_name()+ '_' + timestamp_path,alias_path)

                                            _scp_with_ssh.create_dir_to_local(self.__environment_provider.is_windows(server_info['OS_TYPE']),_temp_backup_path)

                                        else:
                                            root_dir  = server_info['TCAPPL_ROOT_DIR']

                                            _temp_backup_path = os.path.join(_target_path,self.__environment_provider.get_environment_name()+ '_' + timestamp_path,alias_path)
                                            _scp_with_ssh.create_dir_to_local(False,_temp_backup_path)

                                        for infra_file in alias_path_files:
                                        
                                            _src_file = root_dir + infra_file

                                            head, tail = os.path.split(infra_file)

                                            _scp_with_ssh.create_dir_to_local(False,_temp_backup_path + head)

                                            copyfilesresult = _scp_without_ssh.copy_from_remote(_src_file,_temp_backup_path + head)
                                            self._processes.append({'NODE':server_info['NODE'],'process': copyfilesresult,'module': self.__module_label, 'package_id': '', 'label': f"[Infra update]"})

                                            self.__console_msg(copyfilesresult,f'{alias_path} Infra files Backuped')

                else:
                    self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {__class__.__name__} Skipped")

            except Exception as exp:
                self.log.error(exp)
                self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': '', 'label': f"[Infra update]"})
        return self._processes

        
    def _build_arguments(self, bksource, bkfilename, target_path, server_info, action_msg, module_name, _excludes):
        
        try:
            if self._backupUtilities.set_backup_source(bksource, server_info, action_msg):
                self._backupUtilities.set_backup_filename(bkfilename)            
                self._backupUtilities.set_backup_dest(target_path, server_info)
                
                self._backupUtilities.set_backup_env(server_info, _excludes)            
                _command = self._backupUtilities.get_backup_command()     

                if self._parallel:
                    result = self._execute(_command, target_path)
                    #self._processes.append(result)
                    self._processes.append({'NODE':server_info['NODE'],'process':result,'module':module_name, 'label': action_msg})
                    self._processesLabel.append(action_msg)
                else:
                    self.log.info("Please wait while taking 10 to 15 minutes...")
                    result = self._execute(_command, target_path)
                    self.__console_msg(result, action_msg)              

        except Exception as exp:
            self.log.error(f"Backup Failed {exp}")

    def nosso(self):
        self.log.info("NoSSO Server Backup")
        self._parallel = True
        self._overallbackup = True
        self._executeCombineTargets() 
        self._execute_process()

    def mig(self):
        self.log.info("Migration Server Backup")
        self._parallel = True
        self._overallbackup = True
        self._executeCombineTargets()
        self._execute_process()

    def corp(self):
        self.log.info("Corporate Server Backup")
        self._parallel = True
        self._overallbackup = True
        self._executeCombineTargets()
        self._execute_process()

    def db(self):
        self._parallel = False
        self.log.info("Database Backup")
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__target).split(',')):
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name
                if dynamicExecutor.get_sub_module_name():    
                    getattr(Backup, dynamicExecutor.get_sub_module_name())(self)
                else:
                    dynamicExecutor.run_module()
        except Exception as exp:
            self.log.error(exp)
        


    def _executeCombineTargets(self):
        try:
            if self._overallbackup:
                _targetList = self.__environment_provider.resume_state_execution_read(self._tcpackage_id,self.__target,self._resumestate)
            else:
                _targetList = self.__environment_provider.get_execute_targets(self.__target).split(',')

            for threadcount, targets in enumerate(_targetList):
                if self._overallbackup:
                    server_info = self.__environment_provider.update_serverinfo_data(_targetList[targets],self.__arguments)                    
                    if 'executionServer' in self.__arguments._properties[targets]:
                        self.__arguments._environment[self.__arguments._properties[targets]['executionServer']] = server_info
                self.__target = targets
                dynamicExecutor = DynamicExecutor(self.__arguments) 
                dynamicExecutor.set_module_instance(targets) # module instance name
                if dynamicExecutor.get_sub_module_name():    
                    getattr(Backup, dynamicExecutor.get_sub_module_name())(self)
                else:
                    dynamicExecutor.run_module()
            if self._parallel and not self._overallbackup:
                output = [p['process'].wait() for p in self._processes] 
                for resultindex, result in enumerate(output):
                    self.__console_msg(result, self._processes[resultindex]['label'])
        except Exception as exp:
            self.log.error(exp)


        
    def _executeTargets(self):

        try:
            _targetList = self.__environment_provider.resume_state_execution_read(self._tcpackage_id,self.__module_name,self._resumestate)
            
            for threadcount, targets in enumerate(_targetList): 

                server_info = self.__environment_provider.update_serverinfo_data(_targetList[targets],self.__arguments)

                if 'executionServer' in self.__arguments._properties[targets]:
                    self.__arguments._environment[self.__arguments._properties[targets]['executionServer']] = server_info

                # Execute with multiple targets
                if not self.__sub_module_name:
                    self.__target = targets
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_environment(self.__arguments._environment)
                    dynamicExecutor.set_module_instance(targets) # module instance name                    
                    if dynamicExecutor.get_sub_module_name():                        
                        getattr(Backup, dynamicExecutor.get_sub_module_name())(self)
                    else:
                        dynamicExecutor.run_module()                     
        except Exception as exp:
            self.log.error(exp)

    def _execute_process(self):

        self.log.info("Please wait while taking 10 to 15 minutes...")

        def _parallel_result(process, action_msg):
            if len(self.__sub_module_name):
                module_name = self.__module_name +'.'+ '.'.join(self.__sub_module_name)
                result = self.__environment_provider.resume_state_execution_write(self._tcpackage_id,module_name,process['module'],[process],self._parallel)
            else:
                result = self.__environment_provider.resume_state_execution_write(self._tcpackage_id,self.__module_name,process['module'],[process],self._parallel)
            self.__console_msg(result,action_msg)

        process = Process('')
        process.thread_execute(self._processes, _parallel_result)
           
    def _execute(self, command, path='', stderr = True):
        """
         Used to process services/command
        """
        process = Process(command)
        process.set_parallel_execution(self._parallel)
        process.set_stderr(stderr)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            Loggable.log_success(self, f"{action_msg} Successfully.")
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')
