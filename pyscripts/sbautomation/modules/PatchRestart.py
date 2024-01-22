import os
from argparse import Namespace
from corelib.DynamicImporter import DynamicImporter
from corelib.Environment import Environment
from corelib.Loggable import Loggable
from datetime import datetime, timedelta
from corelib.DynamicExecutor import DynamicExecutor
from corelib.Constants import Constants
from corelib.Notification import Notification
from corelib.Table import Table

class PatchRestart(Loggable):

    def __init__(self, args):

        super().__init__(__name__)
        """
        Get the Environment Specific Values from config json
        """
        self.__environment = args._environment
        
        """
        Set arguments from DynamicImporter
        """         
        self.__arguments = args

        """
        Get the Module Specific Values from config json
        """
        self.__properties = args._properties

        """
        Get the Start Stop services lists from config json
        """
        self.__start_services = args._start_services

        self.__stop_services = args._stop_services
        
        self.__manage_services = args._manage_services

        """
        Action from user commandline (Status, Start, Stop)
        """
        self.__action = args._arguments.action
        
        
        """
        Operation of command like (start, status, stop)
        """
        self.__operation = None

        """
        Module name with submodule from user commandline (full name)
        """
        self.__module = args._arguments.module
        self.__module_label = self.__module

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
        Get Instances from config json, based on that the module will execute
        """
        self.__instances = args._instances

        """
        For python package name
        """
        self._package_info = args._package_info

        """
        Operation of command like (start, status, stop)
        """
        self.__operation = None

        """
        Print Services information when triggered the dita command without module
        """
        self.__print_services = args._print_services

        self.__call_back_count = args._call_back_count

        """
        Print Services Results are stored into results
        """
        self.__results = []

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
        Execution Command
        """
        self.__command = None

        """
        Check if header is Printed
        """
        self.__header_printed = False

    def default(self):
        """
        Default method runs when get the print services
        """
        self.__results = []
        self.__action = 'Status'
        self.Status()    
        return self.__results
        

    def Start(self):       
        
        self.__operation = "start" 

        self.get_patch_dates()
        

    def Stop(self):
        
        self.__operation = "stop"
        self.__results = []
        self.get_patch_dates()
        return self.__results
        

    def Status(self):
    
        self.__operation = "status"        
        self.__results = []
        self.get_patch_dates()
        return self.__results
        
    def get_patch_dates(self):
    
        self.log.info("Checking Patch Dates")
        
        try:
            execute_servers = []
            
            execute_servers = list(filter(lambda x: x['NODE'] == 'APP1_IF', self.__instances['FSC']['INSTANCES']))
                        
            _system_keepass_data = self.__arguments._keepass['Jenkins'][0]['entries']

            _patch_sheet_url = os.path.join(self.__environment_provider.get_share_root_path(), [item for item in _system_keepass_data if item.get('title') == 'SYSTEMLINE_PATCH_DATES_SHEET_URL'][0]['url'])
                    
            for inscount, instance in enumerate(execute_servers):
                
            
                _execute_servers = self.__environment_provider.get_execute_server_details(instance['NODE'])
                
                _jenkins_servers = self.__environment_provider.get_execute_server_details('JENKINS_SERVER')

                _notification = Notification(self.__environment_provider.get_ssh_command(_jenkins_servers[0]))               
                
                patchdataArr = self.__environment_provider.read_excel_sheet(_patch_sheet_url, 'Sheet1') 
                
                all_records = self.get_filtered_patch_dates(patchdataArr,all_status=True)
                
                self.get_patch_status_table(all_records, Table())
                
                # Filter records where 'Environment', 'PatchStartDate' and 'Status == Pending' matches
                pending_records = self.get_filtered_patch_dates(patchdataArr, 'Pending')
                #self.get_patch_status_table(pending_records, Table())
                
                # Filter records where 'Environment', 'PatchStartDate' and 'Status == Stopped' matches
                stopped_records = self.get_filtered_patch_dates(patchdataArr, 'Stopped')
                #self.get_patch_status_table(stopped_records, Table())           
                
                # Filter records where 'Environment', 'PatchStartDate' and 'Status == Completed' matches
                completed_records = self.get_filtered_patch_dates(patchdataArr, 'Completed')
                #self.get_patch_status_table(completed_records, Table())
                
                
                # Patch Updates
                if self.__operation == 'stop':
                    self.patch_updates(_patch_sheet_url, pending_records, 'Pending', _system_keepass_data, _notification)
                if self.__operation == 'start':
                    self.patch_updates(_patch_sheet_url, stopped_records, 'Stopped', _system_keepass_data, _notification) 
        
        except Exception as exp:
            self.log.error(exp)                

            
    def patch_updates(self, _patch_sheet, patch_dates, patch_type, system_keepass_data, notification):
    
        if len(patch_dates) > 0:
        
            _patch_date = None
            _patch_time = None
        
            for patch_record in patch_dates:
            
                if patch_type == 'Pending':
                
                    _patch_date = patch_record['PatchStartDate']
                    _patch_time = patch_record['PatchStartTime']
                    
                if patch_type == 'Stopped':
                
                    _patch_date = patch_record['PatchEndDate']
                    _patch_time = patch_record['PatchEndTime']
                
                if _patch_date != '' and _patch_time != '':
                    # Convert 'PatchDate' string to a date object
                    patch_date = datetime.strptime(_patch_date, '%Y-%m-%d %H:%M:%S').date()
                    
                    # Convert 'PatchStartTime' string to a datetime object
                    patch_time = datetime.strptime(_patch_time, '%H:%M:%S').time()                   
                    
                    system_patch_datetime = datetime.combine(patch_date, patch_time)       
                                                          
                    if patch_type == 'Pending':
                        # Subtract 10 minutes from the datetime object (Range dates before and after)
                        lower_limit = system_patch_datetime - timedelta(minutes=30)                    
                        upper_limit = system_patch_datetime - timedelta(minutes=1)
                        
                    
                    if patch_type == 'Stopped':
                        # Add 10 minutes from the datetime object (Range dates before and after)
                        lower_limit = system_patch_datetime + timedelta(minutes=15)                    
                        upper_limit = system_patch_datetime + timedelta(minutes=30)    

                    notification_urls = list(filter(lambda item: 'TEAMS_NOTIFICATON_URL_IRMDEV' in item.get('title'), system_keepass_data))
            
                    notification_urls = notification_urls + list(filter(lambda item: 'TEAMS_NOTIFICATON_URL_IRM' in item.get('title'), system_keepass_data))                   
                                       
                    if patch_type == 'Pending':
                        # Get the current time
                        current_time_pending = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Pending
                        self.log.info(current_time_pending)
                        #current_time_pending = datetime.strptime('2023-12-21 23:40:00', '%Y-%m-%d %H:%M:%S')
                        self.log.info(f"HostName : {patch_record['HostName']}")
                        self.log.info(f"Status : {patch_record['Status']}")
                        self.log.info(f"Current Time Pending: {current_time_pending}")
                        self.log.info(f"System Patch Time Pending: {system_patch_datetime}\n")
                        
                        
                        
                        if lower_limit <= current_time_pending <= upper_limit:
                            self.log.info("Send Team Notification")
                            for notification_url in notification_urls: 
                                _notification_content = f'{{"text": "<b>{self.__environment_provider.get_environment_name()} System Patch - System Down </b></br>Dear All,</br>Please note that <b>{self.__environment_provider.get_environment_name()}</b> system will be down <b>{lower_limit}</b> for Patch Restart Activities.</br>We will share further information once all activities are done.</br>Thanks & Regards</br>IRM Team"}}'
                                notification.send_notification(_notification_content,notification_url['url'])                                
                            """
                            TC Service Shutdown when patch start date and time reached before 30 min
                            """                            
                            # update the lastupdated cell value by column name and row_index
                            # Requesting to stopping the TC Services Status Updated into Stopping                            
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'Status', patch_record['row_index'], 'Stopping')
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'LastUpdated', patch_record['row_index'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            dynamicExecutor = DynamicExecutor(self.__arguments)
                            for service_name in self.__stop_services:
                                serviceData = dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Stop', service_name) # Stop                              
                                    
                            self.__environment_provider.wait_execute(5)
                            # After Service Stopped, Status Updated into Stopped
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'Status', patch_record['row_index'], 'Stopped')
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'LastUpdated', patch_record['row_index'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        
                    if patch_type == 'Stopped':
                        # Get the current time
                        current_time_stopped = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Stopped
                        self.log.info(current_time_stopped)
                        #current_time_stopped = datetime.strptime('2023-12-21 01:46:00', '%Y-%m-%d %H:%M:%S')
                        self.log.info(f"HostName : {patch_record['HostName']}")
                        self.log.info(f"Status : {patch_record['Status']}")
                        self.log.info(f"Current Time Stopped: {current_time_stopped}")
                        self.log.info(f"System Patch Time Stopped: {system_patch_datetime}")
                        if upper_limit >= current_time_stopped >= lower_limit:
                            self.log.info("Send Team Notification")
                            for notification_url in notification_urls: 
                                _notification_content = f'{{"text": "<b>{self.__environment_provider.get_environment_name()} System Patch - System Up</b></br>Dear All,</br>Patch Deployment activity on <b>{self.__environment_provider.get_environment_name()}</b>  has been completed. We have released System.</br>System is up & running.</br>Thanks & Regards</br>IRM Team"}}'
                                notification.send_notification(_notification_content,notification_url['url'])
                            """
                            TC Service Startup when patch restart completed date and time reached after 15 minutes
                            """
                            # update the lastupdated cell value by column name and row_index
                            # Requesting to Starting the TC Services Status Updated into Starting
                            self.__environment_provider.wait_execute(5)
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'Status', patch_record['row_index'], 'Starting')
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'LastUpdated', patch_record['row_index'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            
                            dynamicExecutor = DynamicExecutor(self.__arguments)
                            for service_name in self.__start_services:
                                serviceData = dynamicExecutor.run_service(Constants.PACKAGEINFO_STARTSTOP, 'Start', service_name)  # Start                          
                            # After Service Starting, Status Updated into Started
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'Status', patch_record['row_index'], 'Started')
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'LastUpdated', patch_record['row_index'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            self.__environment_provider.wait_execute(5)
                            # After Service Started, Status Updated into Completed
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'Status', patch_record['row_index'], 'Completed')
                            _record_update_status = self.__environment_provider.write_excel_sheet(_patch_sheet, 'Sheet1', 'LastUpdated', patch_record['row_index'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    
    
    def get_patch_status_table(self, patch_dates, table):
    
        """
        Print the Patch dates with status in table format
        """    
        if len(patch_dates) > 0:
            table.set_column_widths([3, 5, 10, 25, 30, 30, 20, 30, 30, 10, 30])
            table.add_row(['Row','S.No', 'Environment', 'Hostname', 'PatchStartDate', 'PatchStartTime', 'Patching Hours(hrs)', 'PatchEndDate', 'PatchEndTime', 'Status', 'LastUpdated'])
            for patch_record in patch_dates:            
                table.add_row([str(patch_record['row_index']), str(patch_record['S.No']), str(patch_record['Environment']), str(patch_record['HostName']), str(patch_record['PatchStartDate']), str(patch_record['PatchStartTime']), str(patch_record['Patching Hours(Hrs)']), str(patch_record['PatchEndDate']), str(patch_record['PatchEndTime']), str(patch_record['Status']), str(patch_record['LastUpdated'])], Constants.TEXT_GREEN)
        else:
            self.log.info("No Patches on Today")       
        
    def get_filtered_patch_dates(self, patch_dates, patch_status='', all_status=False):
    
        """
        patch_dates: This parameter represents a list of dictionaries, each containing patch-related information (such as 'Environment', 'PatchStartDate', etc.).
        
        patch_status: This parameter is used to filter records based on the 'Status' field.
        
        Retrieves the environment name. Presumably, this is an internal method within the class instance, providing the current environment's name.
        """
        if all_status:
        
            return [record for record in patch_dates if record['Environment'] == self.__environment_provider.get_environment_name()]
            
        # Get the current date
        current_date = datetime.today().date()
        
        if patch_status == '':
            # Filter records where 'Environment', 'PatchStartDate' matches
            return [record for record in patch_dates if record['Environment'] == self.__environment_provider.get_environment_name() and datetime.strptime(record['PatchStartDate'], '%Y-%m-%d %H:%M:%S').date() == current_date]
                    
        # Filter records where 'Environment', 'PatchStartDate' and 'Status' matches
        return [record for record in patch_dates if record['Environment'] == self.__environment_provider.get_environment_name() and datetime.strptime(record['PatchStartDate'], '%Y-%m-%d %H:%M:%S').date() == current_date and record['Status'] == patch_status]

        
        
