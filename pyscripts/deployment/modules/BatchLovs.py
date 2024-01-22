"""
BatchLovs deployment activities
"""
import os

from corelib.Loggable import Loggable
from corelib.Process import Process
from corelib.DynamicExecutor import DynamicExecutor
from xml.etree import ElementTree as ET
import glob
from xml.dom import minidom
from corelib.File import Directory
import re
from corelib.Constants import Constants



class BatchLovs(Loggable):
    
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

        """
        Target Instances setup
        """        
        self.__target = None

        """"
        Remote Execution.
        """
        self.__remote_execution = False

        self._processes = []
        self._processesResult = []
        self._parallel = self.__arguments.parallel    
        """
        Scope and target setup based on configuration
        """   
        if self.__sub_module_name:
            self.__target = self.__environment_provider.get_execute_target(self.__module_name, self.__sub_module_name)
        
        
    def default(self):
                
        self.log.info("BatchLovs Import All")
        return self._executeTargets()           


    def get_namespace(self, element):
        match = re.match(r'\{.*\}', element.tag)
        return match.group(0) if match else ''
    
    def merge_lovs_lang_xml(self, _location_in_package):
        lov_file_names = []
        xml_files = glob.glob(os.path.join(_location_in_package, 'lang')  + "/*.xml")

        if len(xml_files) == 0:
            return False

        xml_file_lang_extensions = []
        [xml_file_lang_extensions.append(x) for x in [os.path.splitext(xml_file)[0][-5:] for xml_file in xml_files] if x not in xml_file_lang_extensions]
        for xml_file_lang_extension in xml_file_lang_extensions:

            tc_lov_xml_add = None
            tc_lov_xml_change = None
            lov_xml_tag = None
            lov_xml_date = None
            batchXSDVersion = None
            lov_xml_add_key = None

            lov_file_name = None

            xml_files_list_by_lang = glob.glob(os.path.join(_location_in_package, 'lang')  + "/*_"+xml_file_lang_extension+".xml")

            for xml_file_list_by_lang in xml_files_list_by_lang:

                tree = ET.parse(xml_file_list_by_lang)
                root = tree.getroot()
                lov_xml_tag = root.tag
                batchXSDVersion = root.get('batchXSDVersion')
                lov_xml_date = root.get('Date') 
                for element in root.iter(lov_xml_tag):
                    if tc_lov_xml_add is None:
                        tc_lov_xml_add = element.find(self.get_namespace(root)+'Add') 
                        lov_xml_add_key = tc_lov_xml_add.find(self.get_namespace(root)+'key')  
                    else:
                        tc_lov_xml_add.extend(element.find(self.get_namespace(root)+'Add') ) 
                        lov_xml_add_key.extend(tc_lov_xml_add.find(self.get_namespace(root)+'key'))
                if tc_lov_xml_add is not None:
                    root = ET.Element(lov_xml_tag, batchXSDVersion=batchXSDVersion, Date=lov_xml_date)
                    root.append(tc_lov_xml_add)
                    ET.register_namespace("", str(self.get_namespace(root).split('}')[0].strip('{')))
                    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent=" ")
                    merged_output = os.path.join(_location_in_package, "merged_output", "lang")
                    if Directory().create(merged_output):
                        lov_file_name = os.path.join(merged_output, "lov_business_data_"+xml_file_lang_extension+".xml")
                        xmlstr = xmlstr.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')
                        with open(lov_file_name, "w", encoding="UTF-8") as f:
                            f.write(xmlstr)

            lov_file_names.append(lov_file_name)
        return lov_file_names

    def merge_lovs_xml(self, _location_in_package):

        xml_files = glob.glob(_location_in_package + "/*.xml")

        if len(xml_files) == 0:
            return False

        tc_lov_xml_add = None
        tc_lov_xml_change = None
        lov_xml_tag = None
        lov_xml_date = None
        batchXSDVersion = None

        lov_file_name = None

        for xml_file in xml_files:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            lov_xml_tag = root.tag
            batchXSDVersion = root.get('batchXSDVersion')
            lov_xml_date = root.get('Date')              

            for element in root.iter(lov_xml_tag):

                if tc_lov_xml_change is None:
                    tc_lov_xml_add = element.find(self.get_namespace(root)+'Add')
                    tc_lov_xml_change = element.find(self.get_namespace(root)+'Change')
                else:
                    tc_lov_xml_add.extend(element.find(self.get_namespace(root)+'Add') )  
                    tc_lov_xml_change.extend(element.find(self.get_namespace(root)+'Change'))

        if tc_lov_xml_add is not None or tc_lov_xml_change is not None:
            root = ET.Element(lov_xml_tag, batchXSDVersion=batchXSDVersion, Date=lov_xml_date)
            root.append(tc_lov_xml_add)
            root.append(tc_lov_xml_change)

            ET.register_namespace("", str(self.get_namespace(root).split('}')[0].strip('{')))
        
            xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent=" ")

            merged_output = os.path.join(_location_in_package, "merged_output")
            if Directory().create(merged_output):
                lov_file_name = os.path.join(merged_output, "lov_business_data.xml")
                xmlstr = xmlstr.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')
                with open(lov_file_name, "w", encoding="UTF-8") as f:                    
                    f.write(xmlstr)
                return lov_file_name 
        
    def Import(self): 
                  
        
        _execute_servers = self.__environment_provider.get_execute_server_details(self.__properties[self.__target]['executionServer'])
        
        for index, server_info in enumerate(_execute_servers):
            """
            Action: customquries
            impotmdoe
            Command:  plmxml_import -u= -g= -pf= -option= -file=
            """
            for tc_package_id in self.__environment_provider.getTCPackageID(self._tcpackage_id):

                try:

                    _location_in_package = self.__environment_provider.get_location_in_package(tc_package_id, self.__properties[self.__target]['location_in_package'])
                    
                    self.log.info(f"{__class__.__name__}")
                    self.log.info("Merging the Lovs Files.....")
                    lov_file_name_urls = self.merge_lovs_xml(_location_in_package)
                    
                    if lov_file_name_urls:

                        lov_file_name_lang_urls = self.merge_lovs_lang_xml(_location_in_package)

                        if lov_file_name_lang_urls:
                            self.log.info(f"BatchLovs Import Started..")
                            command  = self.__build_arguments(server_info,lov_file_name_urls)
                            self.log.info(f"BatchLovs Import Command: {command}")
                            result = self._execute(command, _location_in_package)
                            self._processes.append({'NODE':server_info['NODE'],'process': result,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - {__class__.__name__}"})
                            if not self._parallel:
                                self.__console_msg(result, f"[{tc_package_id}] - {__class__.__name__}")
                        else:
                            self.log.warning(f'Required Lovs Files does not exists! {tc_package_id}. Skipped {__class__.__name__} Deployment')
                    else:
                        self.log.warning(f'Required Lovs Files does not exists! {tc_package_id}. Skipped {__class__.__name__} Deployment')
                except Exception as exp:
                    self.log.error(exp)
                    self._processes.append({'NODE':server_info['NODE'],'process': 1,'module': self.__module_label, 'package_id': tc_package_id,'label': f"[{tc_package_id}] - {__class__.__name__}"})

        return self._processes


    def __build_arguments(self, server_info, file):
        
        __ssh_command = self.__environment_provider.get_ssh_command(server_info)        
    
        if __ssh_command == '':  
            args = []
        else:
            args = [__ssh_command] 

        if self.__environment_provider.get_property_validation('command', self.__properties[self.__target]):
            args.append(self.__properties[self.__target]['command'])

        # Get Infodba Credentials
        args.extend(self.__environment_provider.get_infodba_credentials(server_info))

        # Get Group Name
        args.extend(self.__environment_provider.get_group(server_info))

        if self.__environment_provider.get_property_validation('option', self.__properties[self.__target]):
            args.append('-option='+ self.__properties[self.__target]['option']) 

        args.append('-file='+ file)    
            
        return ' '.join([str(elem) for elem in args])             
        
    def _executeTargets(self):
        try:
            for threadcount, targets in enumerate(self.__environment_provider.get_execute_targets(self.__module_name).split(',')): 
                    # Execute with multiple targets
                if not self.__sub_module_name:   
                    self.__target = targets  
                    dynamicExecutor = DynamicExecutor(self.__arguments)   
                    dynamicExecutor.set_module_instance(targets) # module instance name
                    # calling the targets one by one
                    if dynamicExecutor.get_sub_module_name():
                        _processesResult = getattr(BatchLovs, dynamicExecutor.get_sub_module_name())(self)   
                    else:
                        _processesResult = dynamicExecutor.run_module()   
                    self._processesResult = self._processesResult + _processesResult  
            return self._processesResult            
        except Exception as exp:
            self.log.error(exp)
        
           
    def _execute(self, command, path):

        """ Used to process services/command
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