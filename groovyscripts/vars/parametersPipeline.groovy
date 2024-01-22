
import com.lib.GlobalVars

import com.lib.Utilities

import com.lib.BuildParameters


def call(config) {

    echo '[DEBUG INFO] [ ========[ DITA Deploy Setup Choice Parameters ]======== ]'

    def currentBuidWorkspace = config.currentBuidWorkspace
    def parametersEnable = config.parametersEnable

    def buildParams = new BuildParameters() 
    def utils = new Utilities() 
    
    def parametersList = []

    // Branches
    def branch_options = null
    Map branches = [:]
    def al_branches = [] as ArrayList    
    def branchList = null

    // Environment  
    def environments_options = null
    def al_environments     = [] as ArrayList
    Map environments      = [:]
    def environmentList = null

    // Teamcenter Version
    def tcversion_options = null
    def al_tcversions = [] as ArrayList
    Map tcversions = [:]
    def tcversionList = null

    // Teamcenter Modules
    def tcmodule_options = null
    def al_tcmodules = [] as ArrayList
    Map tcmodules = [:]
    def tcmodulesList = null
    
    // Deployment Targets Options
    def deployment_options  = null
    Map deploymenttargets = [:]
    def al_deploymenttargets  = [] as ArrayList
    def deploymentList = null

    // Deployment Targets Options only DC_ExecuteScripts
    Map deploymentdcexectetargets = [:]
    


    def deploymentsub_options  = null
    Map deploymentsubtargets = [:]
    def al_depsubtargetssubtargets = [] as ArrayList
    def deploymentsubList = null


    def email_options = null    
    Map emails = [:]
    def al_emails = [] as ArrayList
    def emailList = null

    def teams_notify_options = null    
    Map teamsurls = [:]
    def al_teamsurls = [] as ArrayList
    def teamsurlsList = null


    dir(currentBuidWorkspace) {

        

        // if (params.TARGET_ENVIRONMENT != '' || params.TARGET_ENVIRONMENT != null) {
        //     print("Testing Target Name ${params.TARGET_ENVIRONMENT}")
        //     def server_names = utils.readJSONFile("${workspace}/.config/servers/${params.TARGET_ENVIRONMENT}.environment.json")            
        //     println("Name: ${server_names.DCSCRIPT_AWC_ALL.executeServers}")

        // }

        // Branch 
        branch_options = readYaml file: "${workspace}/.config/choices/load-branches-lists.yaml"
        for (element in branch_options) {
            al_branches.add("${element.key}")
            def listVal = branch_options."${element.key}".collect{ '"' + it + '"'}
            branches.put("${element.key}", listVal)
        }
        branchList = al_branches.collect{ '"' + it + '"'}

        // Environment
        environment_options = readYaml file: "${workspace}/.config/choices/load-environment-list.yaml"
        for (element in environment_options) {
            al_environments.add("${element.key}")
            def listVal = environment_options."${element.key }".collect { '"' + it + '"' }
            environments.put("${element.key}", listVal)
        }
        environments.put('No Environment Selected', 'None')
        environmentList = al_environments.collect { '"' + it + '"' }


        // Teamcenter Version
        tcversion_options = readYaml file: "${workspace}/.config/choices/load-tcversions-list.yaml"
        for (element in tcversion_options) {
            al_tcversions.add("${element.key}")
            def listVal = tcversion_options."${element.key}".collect{ '"' + it + '"'}
            tcversions.put("${element.key}", listVal)
        }
        tcversionList = al_tcversions.collect{ '"' + it + '"'}


        tcmodule_options = readYaml file: "${workspace}/.config/choices/load-modules-list.yaml"
        for (element in tcmodule_options) {
            al_tcmodules.add("${element.key}")
            def listVal = tcmodule_options."${element.key}".collect{ '"' + it + '"'}
            tcmodules.put("${element.key}", listVal)
        }
        tcmodulesList = al_tcmodules.collect{ '"' + it + '"'}
        

        // Deployment Targets
        deployment_options = readYaml file: "${workspace}/.config/choices/load-deployment-options.yaml"
        for (element in deployment_options) {
            al_deploymenttargets.add("${element.key}")
            def listVal = deployment_options."${element.key }".collect { '"' + it + '"' }
            deploymenttargets.put("${element.key}", listVal)
            def listDCExec = [] as ArrayList

            listVal.eachWithIndex { item, index ->
            // for (list in listVal) {
                if (index == 0) {
                    listDCExec.add('"DC_Package_Transfer"')
                }
                if (item.contains("DC_ExecuteScripts")) {
                    listDCExec.add(item)
                }               
            }
            deploymentdcexectetargets.put("${element.key}", listDCExec)
        }
        deploymentList = al_deploymenttargets.collect { '"' + it + '"' }

        //print(deploymenttargets['"' + params.TARGET_ENVIRONMENT+ '"'])
        //print(deploymentdcexectetargets)

        // Deployment SubTargets
        deploymentsub_options  = readYaml file: "${workspace}/.config/choices/load-targets-list.yaml"
        for (element in deploymentsub_options) {
            al_depsubtargetssubtargets.add("${element.key}")
            def listVal = deploymentsub_options."${element.key }".collect { '"' + it + '"' }
            deploymentsubtargets.put("${element.key}", listVal)
        }
        deploymentsubList = al_depsubtargetssubtargets.collect { '"' + it + '"' }

        // Emails
        email_options = readYaml file: "${workspace}/.config/choices/load-emails-list.yaml"
        for (element in email_options) {
            al_emails.add("${element.key}")
            def listVal = email_options."${element.key}".collect{ it }
            emails.put("${element.key}", listVal)
        }
        emailList = al_emails.collect { '"' + it + '"' }


        
        // Teams
        teams_notify_options = readYaml file: "${workspace}/.config/choices/load-teams-notification-channels.yaml"
        for (element in teams_notify_options) {
            al_teamsurls.add("${element.key}")
            def listVal = teams_notify_options."${element.key}".collect{ it }
            teamsurls.put("${element.key}", listVal)
        }
        teamsurlsList = al_teamsurls.collect { '"' + it + '"' }


        def startstopList = ["Status_System", "Stop_System", "Start_System"]

        def deployTypeList = ["Full", "Delta"]

        def timedelayList = ["0", "5", "10", "15", "30", "45", "60", "90", "120"]

        startstopList = startstopList.collect { '"' + it + '"' }

        deployTypeList = deployTypeList.collect { '"' + it + '"' }

        timedelayList = timedelayList.collect { '"' + it + '"' }

        parametersEnable.each{ data-> 

            if (data == 'GIT_BRANCH') 
                parametersList.add(buildParams.createCascadeChoiceParameter('GIT_BRANCH', branchList, 'PT_SINGLE_SELECT', 'Select the branch from the Dropdown List'))
            
            if (data == 'TARGET_ENVIRONMENT') 
                parametersList.add(buildParams.createCascadeChoiceParameter('TARGET_ENVIRONMENT', environmentList, 'PT_SINGLE_SELECT', 'Select the target environment to deploy'))
            
            if (data == 'TC_VERSION')
                parametersList.add(buildParams.createCascadeChoiceParameter('TC_VERSION', tcversionList, 'PT_SINGLE_SELECT', 'Select the Teamcenter Version To Build'))  

            if (data == 'STARTSTOP_OPTION')
                parametersList.add(buildParams.createCascadeChoiceParameter('STARTSTOP_OPTION', startstopList, 'PT_SINGLE_SELECT', 'Select the Teamcenter Version To Build'))

            if (data == 'DEPLOY_TYPE')
                parametersList.add(buildParams.createCascadeChoiceParameter('DEPLOY_TYPE', deployTypeList, 'PT_SINGLE_SELECT', 'Select the Deployment Type (Full or Delta)'))  

            if (data == 'TIME_DELAY')
                parametersList.add(buildParams.createCascadeChoiceParameter('TIME_DELAY', timedelayList, 'PT_SINGLE_SELECT', 'Select the time delay to start the job')) 

            if (data == 'DEPLOYMENT_OPTION') 
                parametersList.add(buildParams.createCascadeChoiceParameterWithReferenced('DEPLOYMENT_OPTION', deploymenttargets, 'PT_CHECKBOX','Select the Deployment Option', 'TARGET_ENVIRONMENT', environmentList))

            if (data == 'DEPLOYMENT_OPTION_MAINTENANCE') 
                parametersList.add(buildParams.createCascadeChoiceParameterWithReferenced('DEPLOYMENT_OPTION', deploymentdcexectetargets, 'PT_CHECKBOX','Select the Deployment Option', 'TARGET_ENVIRONMENT', environmentList))
            
            if (data == 'TEAMCENTER_MODULES')
                parametersList.add(buildParams.createCascadeChoiceParameter('TEAMCENTER_MODULES', utils.getMapValuesFromKey(tcmodules, 'modules'), 'PT_CHECKBOX','Select the desired Module from the dropdown list'))

            if (data == 'SUB_TARGETS_DEPLOYMENT')
                parametersList.add(buildParams.createDynamicParameterWithReferenced('SUB_TARGETS_DEPLOYMENT', deploymentsubtargets, 'ET_FORMATTED_HTML','Select target Option in Environment','DEPLOYMENT_OPTION'))
            
            if (data == 'CMN_CHECK_IF_PACKAGE_EXISTS')
                parametersList.add(buildParams.createBooleanParameter('CMN_CHECK_IF_PACKAGE_EXISTS', true, 'If enables the CMN Package will deploy'))
            
            if (data == 'CMN_PACKAGE_NAME')
                parametersList.add(buildParams.createStringParameter('CMN_PACKAGE_NAME', '', 'Enter the common package'))
            
            if (data == 'BU_CHECK_IF_PACKAGE_EXISTS')
                parametersList.add(buildParams.createBooleanParameter('BU_CHECK_IF_PACKAGE_EXISTS', true, 'If enables the RI Package will deploy'))
            
            if (data == 'BU_PACKAGE_NAME')
                parametersList.add(buildParams.createStringParameter('BU_PACKAGE_NAME', '', 'Enter the BU package'))
            
            if (data == 'PACKAGE_NAME')
                parametersList.add(buildParams.createStringParameter('PACKAGE_NAME', 'Daily', 'Enter the package name'))

            if (data == 'BACKUP_FOLDER_NAME')
                parametersList.add(buildParams.createStringParameter('BACKUP_FOLDER_NAME', 'Backup_TIMESTAMP', 'Enter the Backup folder name (TIMESTAMP is automatically replaced the Current Date with Timestamp)'))

            if (data == 'FOLDER_NAME')
                parametersList.add(buildParams.createStringParameter('FOLDER_NAME', '', 'Enter the DCScript Folder Name (Get from Deployment center console)'))
            
            if (data == 'START_DEPLOY_FROM_BEGINNING')
                parametersList.add(buildParams.createBooleanParameter('START_DEPLOY_FROM_BEGINNING', false, 'If enables the resume state to continue failure targets only next deployment with same package and server'))
            
            if (data == 'DEBUG_EXECUTION_MODE')
                parametersList.add(buildParams.createBooleanParameter('DEBUG_EXECUTION_MODE', false, 'Select the value to set framework to debug Mode'))
            
            if (data == 'BUILD_PACKAGE')
                parametersList.add(buildParams.createBooleanParameter('BUILD_PACKAGE', true, 'Select the value to build package'))
            
            if (data == 'NOTIFY_TEAMS_CHANNEL')
                parametersList.add(buildParams.createBooleanParameter('NOTIFY_TEAMS_CHANNEL', false, 'If enables send email notification'))

            if (data == 'TARGET_TEAMS_CHANNELS') 
                parametersList.add(buildParams.createCascadeChoiceParameter('TARGET_TEAMS_CHANNELS', teamsurlsList, 'PT_CHECKBOX', 'Select the target emails list'))

            if (data == 'EMAILS') 
                parametersList.add(buildParams.createStringParameter('EMAILS', '', 'Please enter any new emails, separated by commas, that are not in the list.'))

            if (data == 'PACKAGE_CREATE_MESSAGE')
                parametersList.add(buildParams.createTextParameter('PACKAGE_CREATE_MESSAGE', 'New Package created on <b>GIT_BRANCH</b> with <b>TC_VERSION</b>.</br></br>Package Information: </br>CMN Package Name: <b>CMN_PACKAGE_NAME</b></br>RI Package Name: <b>RI_PACKAGE_NAME</b>.</br></br>', 'Enter the Package Creation Mail Content (GIT_BRANCH & CMN_PACKAGE_NAME & RI_PACKAGE_NAME is automatically replaced the Selected Branch, TC Version with Package Names)'))

            if (data == 'SYSTEM_DOWN_MESSAGE')
                parametersList.add(buildParams.createTextParameter('SYSTEM_DOWN_MESSAGE', 'Please note that <b>TARGET_ENVIRONMENT</b> system will be down Today from <b>CURRENT_TIME_WITH_DELAY</b> for Automation Daily Deployment Activities.</br>We will share further information once all activities are done.</br></br>', 'Enter the System Down Mail Content (TARGET_ENVIRONMENT & CURRENT_TIME_WITH_DELAY is automatically replaced the Selected Target Environment and Current Time with Time Delay)'))

            if (data == 'SYSTEM_UP_MESSAGE')
                parametersList.add(buildParams.createTextParameter('SYSTEM_UP_MESSAGE','Automation Deployment activity on <b>TARGET_ENVIRONMENT</b> has been completed. We have released System.</br> System is up & running.</br></br>', 'Enter the System Up Mail Content (TARGET_ENVIRONMENT is automatically replace the Selected Target Environment)'))

            if (data == 'BUILD_HEADER')
                parametersList.add(buildParams.createSeparatorParameter('BUILD_HEADER','Build Parameters'))

            if (data == 'DEPLOY_HEADER')
                parametersList.add(buildParams.createSeparatorParameter('BUILD_HEADER','Deploy Parameters'))

            if (data == 'NOTIFICATION_HEADER')
                parametersList.add(buildParams.createSeparatorParameter('NOTIFICATION_HEADER','Notification Parameters'))

        }     
  
        properties([parameters(parametersList)])
    }

    return [ 
       'branchesConfig': [
            'branchList': branchList,
            'branch_options': branch_options,
            'branches': branches
        ],
        'environmentConfig': [
            'environmentList': environmentList,
            'environment_options': environment_options,
            'environments': environments
        ],
        'tcversionConfig': [
            'tcversionList': tcversionList,
            'tcversion_options': tcversion_options,
            'tcversions': tcversions
        ],
        'tcmodulesConfig': [
            'tcmodulesList': tcmodulesList,
            'tcmodule_options': tcmodule_options,
            'tcmodules': tcmodules
        ],
        'deploymenttargetsConfig': [
            'deploymentList': deploymentList,
            'deployment_options': deployment_options,
            'deploymenttargets': deploymenttargets,
            'deploymentdcexectetargets': deploymentdcexectetargets
        ],
        'deploymentsubConfig':[
            'deploymentsubList': deploymentsubList,
            'deploymentsub_options': deploymentsub_options,
            'deploymentsubtargets': deploymentsubtargets
        ],
        'emailConfig':[
            'emailList': emailList,
            'email_options': email_options,
            'emails': emails

        ],
        'notifyConfig':[
            'teamsurlsList': teamsurlsList,
            'teams_notify_options': teams_notify_options,
            'teamsurls': teamsurls

        ]
    ]

}