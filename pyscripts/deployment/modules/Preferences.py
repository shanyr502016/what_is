
"""
Preference deployment activities
"""
from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
import os
from corelib.Constants import Constants
from corelib.File import Directory, File
from deployment.lib.UtilityExecutionSet import UtilityExecutionSet
from deployment.lib.DitaReplacements import DitaReplacements

class Preferences(Loggable):
    
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
        self.__module = args._arguments.module
        self.__module_label = self.__module
        """
        Sub Module name from user commandline (Only Sub Module (classname))
        """
        self.__sub_module_name = args._sub_module_name

        """
        Target Teamcenter Package ID get from user commandline
        """        
        self._tcpackage_id = args._tcpackage_id

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel

        """
        Target Instances setup
        """        
        self.__target = None

        self._ditaReplacements = DitaReplacements(self.__environment_provider)

        """
        Remote Execution.
        """
        self.__remote_execution = False 
        
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__scope = self.__sub_module_name[1:][0]
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self):
                
        self.log.info("Preferences Import All")
        return self._executeTargets()           
   
        
    def Override(self):           
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])

         
        for index, server_info in enumerate(_execute_servers):
            """
            Action: Override
            Scope: SITE
            Mode: Import
            Command:  preferences_manager -u= -g= -pf= -mode=import -scope=SITE -action= -file=
            """
            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                _replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()

                _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, _replacement_foldername)

                _excludes_replacements = []

                if 'excludes_replacements' in self.__properties[self.__target]:
                
                    _excludes_replacements = self.__properties[self.__target]['excludes_replacements']
                    
                _loc_package = '/'.join(self.__properties[self.__target]['location_in_package'].split('/')[:2])
                
                _replacement_status = self._ditaReplacements._getDitaProperties(tc_package_id, server_info,_loc_package,_excludes_replacements, self._parallel)
                
                if _replacement_status == 0:
                    
                    if os.path.exists(os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package'])):  

                        _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package']))
                        
                        if self.__properties[self.__target]['scope']=='SITE':
                            __commands = []
                            action = 'import'
                            if os.path.exists(_location_in_package):
                                for file in os.listdir(_location_in_package):
                                        path = _location_in_package
                                        if file.endswith('.xml'):
                                            command  =' '.join([str(elem) for elem in self.__build_arguments(server_info, action)])+' '+'-file="'+path+'/'+file + '"'
                                            self.log.info(f"{self.__target}")
                                            self.log.info(f"Execution Scope: {self.__properties[self.__target]['scope']}")
                                            self.log.info(f"Execution Command: {command}") 
                                            __commands.append(command)                                    
                                        elif os.path.exists(os.path.join(_location_in_package, 'site_dependent')):
                                            self.log.info('SiteDependent')
                                            path = _location_in_package+'/'+'site_dependent'
                                            for file in os.listdir(path):
                                                if file == 'sm4_'+self.__environment_provider.get_environment_name()+'_preference.xml':                                            
                                                    command  = ' '.join([str(elem) for elem in self.__build_arguments(server_info, action)])+' '+'-file="'+path+'/'+file + '"'
                                                    self.log.info(f"{self.__target}")
                                                    self.log.info(f"Execution Scope: {self.__properties[self.__target]['scope']}")
                                                    self.log.info(f"Execution Command: {command}")
                                                    __commands.append(command)
                                if __commands:
                                    self.setUtilityExecution(__commands, 'Preferences_Override_'+ self.__properties[self.__target]['scope'], tc_package_id, server_info) 
                            else:
                                self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {self.__target} Skipped")
        
                        """
                        Action: Override
                        Scope: GROUP
                        Mode: Import
                        Command:  preferences_manager -u= -g= -pf= -mode=import -scope=GROUP -action= -file=
                        """
                        if self.__properties[self.__target]['scope']=='GROUP':
                            __commands = []
                            action = 'import'
                            if os.path.exists(_location_in_package):
                                for target in os.listdir(_location_in_package):
                                    path = _location_in_package+'/'+target
                                    if os.path.isdir(path):
                                        for file in os.listdir(path):
                                            if file.endswith('.xml'):                                        
                                                command  = ' '.join([str(elem) for elem in self.__build_arguments(server_info, action)])+' '+'-target="'+target+'" '+'-file="'+path+'/'+file + '"'
                                                self.log.info(f"{self.__target}")
                                                self.log.info(f"Execution Scope: {self.__properties[self.__target]['scope']}")
                                                self.log.info(f"Execution Command: {command}")
                                                __commands.append(command)
                                if __commands:
                                    self.setUtilityExecution(__commands, 'Preferences_Override_'+ self.__properties[self.__target]['scope'], tc_package_id, server_info) 
                            else:
                                self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {self.__target} Skipped")
                        

                        """
                        Action: Override
                        Scope: ROLE
                        Mode: Import
                        Command:  preferences_manager -u= -g= -pf= -mode=import -scope=ROLE -action= -file=
                        """
                        if self.__properties[self.__target]['scope']=='ROLE':
                            __commands = []
                            action = 'import'
                            if os.path.exists(_location_in_package):
                                for target in os.listdir(_location_in_package):
                                    path = _location_in_package+'/'+target
                                    if os.path.isdir(path):
                                        for file in os.listdir(path):
                                            if file.endswith('.xml'):                                        
                                                command  = ' '.join([str(elem) for elem in self.__build_arguments(server_info, action)])+' '+'-target="'+target+'" '+'-file="'+path+'/'+file + '"'
                                                self.log.info(f"{self.__target}")
                                                self.log.info(f"Execution Scope: {self.__properties[self.__target]['scope']}")
                                                self.log.info(f"Execution Command: {command}")
                                                __commands.append(command)
                                if __commands:
                                    self.setUtilityExecution(__commands, 'Preferences_Override_'+ self.__properties[self.__target]['scope'], tc_package_id, server_info) 
                            else:
                                self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {self.__target} Skipped")

                    else:
                        self.log.warning(f'Replacement Environment is not avaliable in {tc_package_id}') 
                        self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Preferences Override"})
        
        return self._processes

   
        
    def Merge(self):
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        
        for index, server_info in enumerate(_execute_servers):
            
            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):
            
                _replacement_foldername = 'deploy_'+self.__environment_provider.get_environment_name().lower()

                _replacement_path = self.__environment_provider.get_location_in_package(tc_package_id, _replacement_foldername)

                _excludes_replacements = []

                if 'excludes_replacements' in self.__properties[self.__target]:
                
                    _excludes_replacements = self.__properties[self.__target]['excludes_replacements']
                    
                _loc_package = '/'.join(self.__properties[self.__target]['location_in_package'].split('/')[:2])
                
                _replacement_status = self._ditaReplacements._getDitaProperties(tc_package_id, server_info,_loc_package,_excludes_replacements, self._parallel)
                
                if _replacement_status == 0:
                    
                    if os.path.exists(os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package'])):

                        _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, os.path.join(_replacement_path,self.__properties[self.__target]['location_in_package']))
                        """
                        Action: MERGE
                        Scope: SITE
                        Mode: Import
                        Command:  preferences_manager -u= -g= -pf= -mode=import -scope=SITE -action= -file=
                        """
                        if self.__properties[self.__target]['scope']=='SITE':
                            __commands = []
                            action = 'import'
                            if os.path.exists(_location_in_package):
                                for file in os.listdir(_location_in_package):
                                    if file.endswith('.xml'):                                
                                        command  = ' '.join([str(elem) for elem in self.__build_arguments(server_info, action)])+' '+'-file="'+_location_in_package+'/'+file + '"'
                                        self.log.info(f"{self.__target}")
                                        self.log.info(f"Execution Scope: {self.__properties[self.__target]['scope']}")
                                        self.log.info(f"Execution Command: {command}")
                                        __commands.append(command)
                                if __commands:
                                    self.setUtilityExecution(__commands, 'Preferences_Merge_'+ self.__properties[self.__target]['scope'], tc_package_id, server_info) 
                            else:
                                self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {self.__target} Skipped")

                        """
                        Action: MERGE
                        Scope: ROLE
                        Mode: Import
                        Command:  preferences_manager -u= -g= -pf= -mode=import -scope=ROLE -action= -file=
                        """
                        if self.__properties[self.__target]['scope']=='ROLE':
                            __commands = []
                            action = 'import'
                            if os.path.exists(_location_in_package):
                                for target in [ name for name in os.listdir(_location_in_package) if os.path.isdir(os.path.join(_location_in_package, name)) ]:
                                    self.log.info(target)
                                    for file in os.listdir(os.path.join(_location_in_package, target)):
                                        if file.endswith('.xml'):
                                            #command  = ' '.join([str(elem) for elem in self.__build_arguments(server_info, action)])+' '+'-target="'+target+'" '+'-file="'+os.path.join(_location_in_package, target, file) +'" '+'-scope='+'role'
                                            command  = ' '.join([str(elem) for elem in self.__build_arguments(server_info, action)])+' '+'-target="'+target+'" '+'-file="'+os.path.join(_location_in_package, target, file) +'" '
                                            self.log.info(f"Execution Scope: {self.__properties[self.__target]['scope']}")
                                            self.log.info(f"Execution Command: {command}")
                                            __commands.append(command)
                                if __commands:
                                    self.setUtilityExecution(__commands, 'Preferences_Merge_'+ self.__properties[self.__target]['scope'], tc_package_id, server_info) 
                                    
                            else:
                                self.log.warning(f"Required File or Folder not Present from this location {tc_package_id}. {self.__target} Skipped")
                    else:
                        self.log.warning(f'Replacement Environment is not avaliable in {tc_package_id}') 
                        self._processes.append({'NODE':server_info['NODE'],'process': 0,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - Preferences Merge"})
        return self._processes


    def setUtilityExecution(self, commands, package_name, tc_package_id, server_info):

        utilityExecution = UtilityExecutionSet(self.__environment_provider, commands, package_name + '_'+ tc_package_id, self._parallel)
        result = utilityExecution.execute()
        self._processes.append({'NODE':server_info['NODE'],'process': result, 'module': self.__module_label, 'package_id': tc_package_id, 'label': f"[{tc_package_id}] - {package_name}"}) 
        if not self._parallel:
            self.__console_msg(result, f"[{tc_package_id}] - {package_name}")            


    def __build_arguments(self, _server_info, _action):
        
        __ssh_command = self.__environment_provider.get_ssh_command(_server_info)
        
        if __ssh_command == '':
            self.__remote_execution = False  
        else:
            self.__remote_execution = True
    
        if self.__remote_execution:
            args = [__ssh_command,
                    self.__properties[self.__target]['command'],
                    '-u='+ _server_info['TC_USER'],
                    '-g='+ _server_info['TC_GROUP'],
                    '-pf='+ _server_info['TC_PWF'],
                    '-mode='+ _action, 
                    '-scope=' + str(self.__scope).upper(),
                    '-action=' + self.__properties[self.__target]['action'],
                ]       
        else:
            args = [self.__properties[self.__target]['command'],
                    '-u='+ _server_info['TC_USER'],
                    '-g='+ _server_info['TC_GROUP'],
                    '-pf='+ _server_info['TC_PWF'],
                    '-mode='+ _action, 
                    '-scope=' + str(self.__scope).upper(),
                    '-action=' + self.__properties[self.__target]['action'],
                ]     
            
        return args        
        
    def _executeTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__module_name).split(',')): 
                # Execute with multiple targets
                if not self.__sub_module_name:
                    self.__target = targets   
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_module_instance(targets) # module instance name
                    self.__scope = dynamicExecutor.get_action()
                    # calling the targets one by one
                    if dynamicExecutor.get_sub_module_name():
                        _processesResult = getattr(Preferences, dynamicExecutor.get_sub_module_name())(self)
                    else:
                        _processesResult = dynamicExecutor.run_module()
                    self._processesResult = self._processesResult + _processesResult  
  
            return self._processesResult              
        except Exception as exp:
            self.log.error(exp)
        
           
    def _execute(self, command, path='/'):
        """
         Used to process services/command
        """
        process = Process(command, path)
        process.set_parallel_execution(self._parallel)
        return process.execute()


    def __console_msg(self, result, action_msg):
        if result == 0:
            self.log.info(Constants.colorize(f"{action_msg} Successfully!.",Constants.TEXT_GREEN))
        else:
            self.log.error(f"{action_msg} Failed.")
        self.log.info('..............................................................')