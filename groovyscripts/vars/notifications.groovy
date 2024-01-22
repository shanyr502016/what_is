
import com.lib.Utilities
import groovy.json.JsonSlurperClassic

def call(config) {

    

    def utils = new Utilities()
    def emails = null    

    if (config instanceof List) {
       return null
    }

    if (!config.containsKey('parametersConfig')) {
        return null
    } else {
        def emailConfig = config.parametersConfig['emailConfig']
        def notifyConfig = config.parametersConfig['notifyConfig']
        teamsurls = notifyConfig['teamsurls']
        emails = emailConfig['emails']
    }
    def options = config.containsKey('options') ? config.options: 'default'
    
    def toaddr = config.containsKey('toaddr') ? config.toaddr: 'SystemAdmin'
    def body = config.containsKey('body') ? config.body: '''${SCRIPT, template="groovy-html.template"}'''
    def subject = config.containsKey('subject') ? config.subject: "${currentBuild.currentResult}: Job ${env.JOB_NAME}"

    def mimeType = config.containsKey('mimeType') ? config.mimeType: 'text/html'
    def replyTo = config.containsKey('replyTo') ? config.replyTo: '$DEFAULT_REPLYTO'
    def attachLog = config.containsKey('attachLog') ? config.attachLog: false
    def compressLog = config.containsKey('compressLog') ? config.compressLog: false

    def downtime = config.containsKey('downtime') ? config.downtime: new Date().format("dd.MM.yyyy", TimeZone.getTimeZone('UTC'))
    def profile = config.containsKey('profile')

    if (profile) { 
        toaddr = utils.getMapValuesFromKey(teamsurls, config.profile).join(',')        
    } else {
        if (params.TARGET_TEAMS_CHANNELS == '' || params.TARGET_TEAMS_CHANNELS == null) {
            toaddr = utils.getMapValuesFromKey(teamsurls, 'SystemAdmin').join(',')
        } else {
            toaddr = utils.getEmailGroupList(teamsurls, params.TARGET_TEAMS_CHANNELS).join(',')
        }
    }


    // if (options == 'default')
    //     return emailext(to: toaddr, mimeType: mimeType, body: body, subject: subject, attachLog: attachLog, compressLog: compressLog, replyTo: replyTo)  
    if (options == 'system_down')   
        return systemDownNotification(toaddr, body, downtime, notify_type='teams') 
    if (options == 'system_up')  
        return systemUpNotification(toaddr, body, notify_type='teams')
    if (options == 'system_error')
        return systemErrorNotification(toaddr, body, subject, notify_type='teams')
    if (options == 'package_create')
        return packageCreateNotification(toaddr, body, subject, notify_type='teams')   
        
}


def systemDownNotification(toaddr, content, downtime, notify_type='email') {  

    def body = """Dear All,</br>"""

    body += content
    body += """Thanks & Regards</br>IRM Team</br>"""
    echo '[DEBUG INFO] Email Notification for System Down'
    String mimeType = 'text/html'
    String subject = "${params.TARGET_ENVIRONMENT} - System Downtime ${downtime}"
    if (notify_type == 'email')
        return emailext(to: toaddr, mimeType: mimeType, body: body, subject: subject, attachLog: false, compressLog: false)
    if (notify_type == 'teams')
        return teamsnotification(toaddr, teams_template(subject, body))  
}

def systemErrorNotification(toaddr, content, subject,notify_type='email') {
    def body = """Dear All,</br>"""
    body += content
    body += """Thanks & Regards</br>IRM Team</br>"""
    echo '[DEBUG INFO] Email Notification for System Up'           
    String mimeType = 'text/html'
    if (notify_type == 'email')
        return emailext(to: toaddr, mimeType: mimeType, body: body, subject: subject, attachLog: false, compressLog: false)
    if (notify_type == 'teams')
        return teamsnotification(toaddr, teams_template(subject, body))   
}

def packageCreateNotification(toaddr, content, subject, notify_type='email') {
    def body = """Dear All,</br>"""
    body += content
    body += """Thanks & Regards</br>IRM Team</br>"""
    echo '[DEBUG INFO] Email Notification for Package Creation'           
    String mimeType = 'text/html'
    if (notify_type == 'email')
        return emailext(to: toaddr, mimeType: mimeType, body: body, subject: subject, attachLog: false, compressLog: false)
    if (notify_type == 'teams')
        return teamsnotification(toaddr, teams_template(subject, body))  
}   


def systemUpNotification(toaddr, content, notify_type='email') {
    print(toaddr)
    def body = """Dear All,</br>"""
    body += content
    body += """Thanks & Regards</br>IRM Team</br>"""
    echo '[DEBUG INFO] Email Notification for System Up'           
    String mimeType = 'text/html'
    String subject = "${params.TARGET_ENVIRONMENT} - System Up"
 
    if (notify_type == 'email')
        return emailext(to: toaddr, mimeType: mimeType, body: body, subject: subject, attachLog: false, compressLog: false)
    if (notify_type == 'teams')
        return teamsnotification(toaddr, teams_template(subject, body))  

}

def teamsnotification(url, teams_message) {

    def jobParameters = [
        [$class: 'StringParameterValue', name: 'INCOMING_WEBGHOOK_URL', value: url],
        [$class: 'StringParameterValue', name: 'TEAMS_MESSAGE', value: teams_message]
    ]

    def notification_status = true
    def notifiation_exec_status = build job: 'DITA_Notification', parameters: jobParameters
    
    if (notifiation_exec_status.getResult() == 'SUCCESS') {
        notification_status = true                                        
    } else {
        notification_status = false
        error 'Notification Failed'
    }
}


def teams_template(subject, body) {
    // return """{"@type": "MessageCard","@context": "http://schema.org/extensions","themeColor": "0076D7","summary": "Notification from PLM@SMO Deployments","sections": [{"activityTitle": "${subject}","activitySubtitle": "${body}","activityImage": ""}]}"""
    return """{"text": "<b>${subject}</b> </br>${body}" }"""
}