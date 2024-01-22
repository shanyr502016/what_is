#!/usr/bin/env groovy
/* groovylint-disable CatchException */
package com.lib
import java.util.Calendar
import java.util.TimeZone
import java.text.SimpleDateFormat

import groovy.json.JsonSlurperClassic

class Utilities {



    def checkDeployTarget(options, selectedOption) {
        options = options.split(',')
        return options.findAll{selectedOption.trim().toLowerCase().equals(it.trim().toLowerCase())}.any{true}
    }

    def checkTargetName(options, selectedOption) { // checkType equals 
        options = options.split(',')
        return options.findAll{selectedOption.trim().toLowerCase().equals(it.trim().toLowerCase())}.any{true}
    }

    def containsTargetName(options, selectedOption) { // checkType contains
        options = options.split(',')
        return options.findAll{it.trim().toLowerCase().contains(selectedOption.trim().toLowerCase())}.any{true}
    }

    def replaceEscapedPath(path) { // Replace Slashes
        def originalPath = path
        def escapedPath = originalPath.replaceAll('\\\\', '\\\\\\\\')        
        return escapedPath
    }

    def filterTargetName(options, keyword) {
        return options.findAll { data ->  data.contains(keyword) }
    }

    def robocopy(cmd) {
        // robocopy uses non-zero exit code even on success, status below 3 is fine
        def status = bat returnStatus: true, script: "ROBOCOPY ${cmd}"        
        return status
    }

    def checkoutTC(repourl, branch, credentialsId) {
        return checkout([$class: 'GitSCM', branches: [[name: '*/' + branch]], 
                extensions: [[$class: 'GitLFSPull']],
                userRemoteConfigs: [[credentialsId: credentialsId, url: repourl]]])
    }

    def readJSONFile(String filePath) {  

        def file = new File(filePath) 

        if (file.exists()) { 
            return new groovy.json.JsonSlurperClassic().parse(file)

        }    
        
        
    }

    
   
    /* Function to fetch the List of values for a particular key from the gieven Map */
    def getMapValuesFromKey(Map map, String key) {
        def listSubModLov = []
        map.each { entry ->
            if ("$entry.key" == key) {
                listSubModLov = entry.value
            }
        }
        return listSubModLov
    }

    def getEmailGroupList(groupEmails, groups) {
        def grouplist = groups.split(',')
        def selectedEmails = []
        grouplist.each { groupname->
            selectedEmails += getMapValuesFromKey(groupEmails,groupname)           
        }
        return selectedEmails.unique()
    }


    def getCurrentTime(delay = 0, format='hh:mm a',zone='CET'){
        // Get the current date and time in the CET time zone
        def timeZone = TimeZone.getTimeZone(zone)
        def calendar = Calendar.getInstance(timeZone)
        def currentDateInCET = calendar.time

        // Format the time
        def sdf = new SimpleDateFormat(format)
        sdf.timeZone = timeZone
        def formattedTime = sdf.format(currentDateInCET)
        // Add 10 minutes
        calendar.add(Calendar.MINUTE, delay)

        // Get the updated date and time
        def updatedDateInCET = calendar.time
        def formattedUpdatedTime = sdf.format(updatedDateInCET)

        // println("Updated CET time after adding 10 minutes: $formattedUpdatedTime")

        return formattedUpdatedTime
    }

    def getMatchingTargets(config, selectedTargets) {

        def matchingTargetsList = [:]

        config['deploymentsubConfig']['deploymentsubList'].each { key->

            key = key.replaceAll('"', '')
            def matchingTargets = []
            getMapValuesFromKey(config['deploymentsubConfig']['deploymentsubtargets'], key).each { target->
                target = target.replaceAll('"', '')

                selectedTargets.each { selectedTarget ->
                    if (target == selectedTarget) {
                        matchingTargets.add(target)
                    }
                }
            }
            matchingTargetsList[key] = matchingTargets

        }      

        return matchingTargetsList
    }


    def handleStatus(statusCode, currentBuild) {
        if (statusCode != '0') {
            currentBuild.result = 'FAILED'
        }
        if (statusCode == '0') {
            currentBuild.result = 'SUCCESS'
        }
    }

    def findJobType(currentBuild) {
        String JOB_NAME = currentBuild.fullProjectName
        def JOB_MATCHER = JOB_NAME =~ /.*_(Dev|Master)/
        String JOB_TYPE = JOB_MATCHER ? JOB_MATCHER[0][1] : 'Unknown'    
        return JOB_TYPE
    }



    // Function to extract hostname from labels
    def getHostNameFromLabels(serverName) {
        try {
            // Find the specific node by name
            def targetNode = Jenkins.instance.getComputer(serverName)
            if (targetNode) {
                def launcher = targetNode.getNode().getLauncher()
                def hostName = (launcher.host).toString().trim()
                return hostName
            }
            return         
        } catch (Exception e) {
            return 
        }     
    }

}

