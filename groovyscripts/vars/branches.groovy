#!/usr/bin/env groovy

def call(config) {

    def configuration = config.configuration
    def shareLocation = config.shareLocation
    def parametersConfig =  config.parametersConfig

    def commonPackageName= config.containsKey('commonPackageName') ? config.commonPackageName: ''
    def buPackageName = config.containsKey('buPackageName') ? config.buPackageName: ''

    String GIT_BRANCH = ""

    def PACKAGE_LIST_TO_DEPLOY = null 

    File cmnPackageDir = null
    File buPackageDir = null

    // Master Branch
    if (commonPackageName.contains('master')) {
        cmnPackageDir = new File(shareLocation + configuration['mastercmnPackageLoaction'] + '/' + commonPackageName)
        GIT_BRANCH = "master"
    }

    if (buPackageName.contains('master')) {
        buPackageDir = new File(shareLocation + configuration['masterbuPackageLoaction'] + '/' + buPackageName)
        GIT_BRANCH = "master"
    }

    // Dev Branch
    if (commonPackageName.contains('dev')) {
        cmnPackageDir = new File(shareLocation + configuration['devcmnPackageLoaction'] + '/' + commonPackageName)
        GIT_BRANCH = "dev"
    }

    if (buPackageName.contains('dev')) {
        buPackageDir = new File(shareLocation + configuration['devbuPackageLoaction'] + '/' + buPackageName)
        GIT_BRANCH = "dev"
    }

    // R1.1 Branch
    if (commonPackageName.contains('R1.1')) {
        cmnPackageDir = new File(shareLocation + configuration['r1cmnPackageLoaction'] + '/' + commonPackageName)
        GIT_BRANCH = "R1.1"
    }

    if (buPackageName.contains('R1.1')) {
        buPackageDir = new File(shareLocation + configuration['r1buPackageLoaction'] + '/' + buPackageName)
        GIT_BRANCH = "R1.1"
    }

    // R1.1.1 Branch
    if (commonPackageName.contains('R1.1.1')) {
        cmnPackageDir = new File(shareLocation + configuration['r11cmnPackageLoaction'] + '/' + commonPackageName)
        GIT_BRANCH = "R1.1.1"
    }

    if (buPackageName.contains('R1.1.1')) {
        buPackageDir = new File(shareLocation + configuration['r11buPackageLoaction'] + '/' + buPackageName)
        GIT_BRANCH = "R1.1.1"
    }

    // R1.2 Branch
    if (commonPackageName.contains('R1.2')) {
        cmnPackageDir = new File(shareLocation + configuration['r2cmnPackageLoaction'] + '/' + commonPackageName)
        GIT_BRANCH = "R1.2"
    }

    if (buPackageName.contains('R1.2')) {
        buPackageDir = new File(shareLocation + configuration['r2buPackageLoaction'] + '/' + buPackageName)
        GIT_BRANCH = "R1.2"
    }

    // POC Branch
    if (commonPackageName.contains('POC')) {
        cmnPackageDir = new File(shareLocation + configuration['poccmnPackageLoaction'] + '/' + commonPackageName)
        GIT_BRANCH = "POC"
    }    

    if (buPackageName.contains('POC')) {
        buPackageDir = new File(shareLocation + configuration['pocbuPackageLoaction'] + '/' + buPackageName)
        GIT_BRANCH = "POC"
    }

    if (config.containsKey('commonPackageName')) {

        // Check the Common Package Directory in the Share location
        try {
            if (cmnPackageDir.exists() && cmnPackageDir.isDirectory()) {
                echo '[DEBUG INFO] commonPackageName : [' + commonPackageName + '] found in the location ' + cmnPackageDir  
                PACKAGE_LIST_TO_DEPLOY = commonPackageName


                // Get Delta Information from Teamcenter Project Reposistory
                // checkoutPipeline([
                //         GIT_REPOURL: configuration['SMO_GIT_URL'], GIT_PROJECT: configuration['SMO_GIT_PROJECT'], 
                //         GIT_BRANCH_NAME: parametersConfig['branchesConfig']['branch_options']."${GIT_BRANCH}"[0], 
                //         GIT_BRANCH: GIT_BRANCH, credentialsId: 'indodbaat47xx'
                // ])

            } else {
                echo '[DEBUG INFO] commonPackageName : [' + commonPackageName + '] not found in the location ' + cmnPackageDir
                if ((params.CMN_CHECK_IF_PACKAGE_EXISTS.equals("true"))) {
                    error 'Common Package Not Available'       
                }
            }
        } catch (Exception e) {            
            echo '[DEBUG INFO] Exception commonPackageName: ' + commonPackageName + ' not found in the location ' + cmnPackageDir        
            if (params.CMN_CHECK_IF_PACKAGE_EXISTS.equals("true")) {
                error 'Common Package Not Available'                   
            }
        }

    }

    if (config.containsKey('buPackageName')) {
        // Check the BU Package Directory in the Share location
        try {
            if (buPackageDir.exists() && buPackageDir.isDirectory()) {
                echo '[DEBUG INFO] buPackageName : [' + buPackageName + '] found in the location ' + buPackageDir
                if (PACKAGE_LIST_TO_DEPLOY == null) {
                    PACKAGE_LIST_TO_DEPLOY = buPackageName
                } else {
                    PACKAGE_LIST_TO_DEPLOY = PACKAGE_LIST_TO_DEPLOY + ',' + buPackageName 
                }
            } else {
                echo '[DEBUG INFO] buPackageName : [' + buPackageName + '] not found in the location ' + buPackageDir
                if (params.BU_CHECK_IF_PACKAGE_EXISTS.equals("true")) {
                    error 'BuPackage Not Available' 
                }
            }
        } catch (Exception e) {
            echo '[DEBUG INFO] Exception buPackageName : [' + buPackageName + '] not found in the location ' + buPackageDir        
            if (params.BU_CHECK_IF_PACKAGE_EXISTS.equals("true")) { 
                error 'BuPackage Not Available'             
            }
        }
    }
    return [ 
        'DITA_SCRIPTS_PATH': shareLocation + configuration['DITA_SCRIPTS_PATH'],
        'DITA_MANAGE_SCRIPTS': shareLocation + configuration['DITA_MANAGE_SCRIPTS'],
        'DITA_DEPLOY_SCRIPTS': shareLocation + configuration['DITA_DEPLOY_SCRIPTS'],
        'DITA_BUILD_SCRIPTS': shareLocation + configuration['DITA_BUILD_SCRIPTS'],
        'CMN_PACKAGE_LOCATION': cmnPackageDir,
        'RI_PACKAGE_LOCATION': buPackageDir,
        'PACKAGE_LIST_TO_DEPLOY': PACKAGE_LIST_TO_DEPLOY
    ]
    
}