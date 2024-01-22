#!/usr/bin/env groovy
package com.lib

import com.lib.Utilities

/**
     * Description Building Jenkins Parameters
     * @param startIndex - the starting index
     * @return the full count
     * @throws RuntimeException if you are not pure of spirit
     *
     * NOTE: Custom Dynamic Parameter need to approve the In-Script Approval from Manage Jenkins
     *
     */
class BuildParameters {

    def createBooleanParameter(name, defaultValue, description) { // Create the Boolean Parameter value True | False @return BooleanParameter
        return [$class: 'BooleanParameterDefinition', name: name, defaultValue: defaultValue, description: description]
    }

    def createStringParameter(name, defaultValue, description) {
        return [$class: 'StringParameterDefinition', name: name, defaultValue: defaultValue, description: description]
    }

    def createTextParameter(name, defaultValue, description) {
        return [$class: 'TextParameterDefinition', name: name, defaultValue: defaultValue, description: description]
    }

    def createChoiceParameter(name, choices, description) {
        return [$class: 'ChoiceParameterDefinition', name: name, choices: choices, description: description]
    }


    def createSeparatorParameter(name, header) {
        return [$class: 'ParameterSeparatorDefinition', 
                name: name, 
                sectionHeader: header,
                separatorStyle: ' background: #999; border-bottom:1px dashed #ccc;',
                sectionHeaderStyle: 'text-align:left; font-size: 17px; font-weight: bold;'
            ]
    }

    /* Create the Boolean Parameter
    * @param name, choices, choiceType, descriptions
    * @return List 
    */
    def createCascadeChoiceParameter(name, choices, choiceType, description) {

        return [$class: 'CascadeChoiceParameter',
                    choiceType: choiceType,
                    description: description,
                    filterLength: 1,
                    filterable: false,
                    name: name,
                    script:[
                        $class: 'GroovyScript',
                        fallbackScript: [classpath: [],sandbox: true, script: "return ['ERROR']" ],
                        script: [classpath: [], sandbox: true, script: """return${choices}""".stripIndent()]
                    ]
            ]
    }

    def createCascadeChoiceParameterWithReferenced(name, choices, choiceType, description, referencedParameters, mappingData) {

        def formattedmappingData = []
        
        mappingData.each{ data-> 
            data = data.replaceAll('"','')
            formattedmappingData.add("'${data}':'${data}'") 
        }            

        def scriptData = """    
                        def referencedParam = ${referencedParameters}                               
                        def formattedmappingData = ${formattedmappingData}
                        def selectedValue = formattedmappingData[referencedParam]
                        def data = []                            
                        if (referencedParam.equals(selectedValue)){
                            ${choices}.each { entry ->
                                if (entry.key == selectedValue) {
                                    data = entry.value
                                }
                        }
                            return data                                
    }
                        """.stripIndent()
        return [$class: 'CascadeChoiceParameter',
                choiceType: choiceType,
                description: description,
                filterLength: 1,
                filterable: false,
                name: name,
                referencedParameters: referencedParameters,
                script:[
                    $class: 'GroovyScript',fallbackScript: [classpath: [],sandbox: true,script: "return ['ERROR']"],
                    script: [classpath: [],sandbox: true,
                            script: scriptData
                            ]
                    ]
        ]
    }

    def createDynamicParameterWithReferenced(name, choices, choiceType, description, referencedParameters) {

        return [
                $class: 'DynamicReferenceParameter',
                choiceType: choiceType,
                description: description,
                omitValueField: true,
                name: name,
                referencedParameters: referencedParameters,
                script: [
                    $class: 'GroovyScript',fallbackScript: [classpath: [],sandbox: true, script: "return ['None']"],
                    script: [classpath: [],sandbox: false,
                        script: """                                                
                            def choices = ${choices}
                            def referencedArr = ${referencedParameters}.split(",")
                            def html_to_be_rendered = "<div>"
                            referencedArr.each { target ->
                            if (choices[target]) {
                                def target_list = choices[target]                                                
                                html_to_be_rendered += "<div style='font-weight:600;margin-top:8px;margin-bottom:8px;'>"+ target +"</div>"
                            
                                target_list.each { data ->
                                    html_to_be_rendered +='<div style="white-space:nowrap"><div>'
                                    html_to_be_rendered +='<input name="value" id="' + data + '" value="' + data + '" alt="' + data + '" title="' + data + '"  json="' + data + '" type="checkbox" checked class=" ">' +
                                                        '<label title=' + data + ' class="attach-previous">' + data + '</label>'
                                    html_to_be_rendered +='</div></div>'        
                                }                                
                            }
                            }
                            html_to_be_rendered += "</div>"                                                
                            return html_to_be_rendered""".stripIndent()
                        ]
                    ]
    ]
    }


}