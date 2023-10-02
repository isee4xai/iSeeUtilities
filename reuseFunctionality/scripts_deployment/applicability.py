import json
import requests

ANY_URI='http://www.w3id.org/iSeeOnto/explainer#Any'
TRANSLATION_URL = " https://api-onto-dev.isee4xai.com/api/onto/cockpit/ExplainerFieldsFlat"



def applicabilityExplainer(case_id, access_token, explainer):
    context=getUseCaseContext(case_id, access_token)
    response = requests.request("GET", TRANSLATION_URL)
    trans_table=json.loads(response.text)
    return checkApplicability(context,explainer,trans_table)  


def getUseCaseContext(case_id, token):
    
    USECASES_URL = "https://api-dev.isee4xai.com/api/usecases/"+case_id
    headers = {'X-Access-Token': token}
    
    response = requests.request("GET", USECASES_URL, headers=headers)
    usecase_info=json.loads(response.text)

    context={}
    context["ai_task"]=usecase_info["settings"]["ai_task"]
    context["ai_method"]=usecase_info["settings"]["ai_method"]
    context["dataset_type"]=usecase_info["settings"]["dataset_type"]
    context["implementation"]=usecase_info["model"]["backend"]
    
    return context


def format_attr(attr,code,key,trans_table):
    if(code==0):
        return trans_table[key][attr]
    elif(code==1):
        if isinstance(attr,list):
            if isinstance(attr[-1],list):
                attr=attr[-1]
            if(len(attr)==1):
                return format_attr(attr[-1],0,key,trans_table)
            i=0
            msg=""
            while i < len(attr)-1:
                msg=msg+format_attr(attr[i],0,key,trans_table)+", "
                i=i+1
            msg=msg[:-2]+" and " + format_attr(attr[i],0,key,trans_table)  
            return msg
        else:
            return format_attr(attr,0,key,trans_table)
    elif(code==3):
        if isinstance(attr,list):
            if isinstance(attr[-1],list):
                attr=attr[-1]
        attr=attr[-1]
        return format_attr(attr,0,key,trans_table)


def checkApplicability(context,explainer,trans_table):
    ANY_URI='http://www.w3id.org/iSeeOnto/explainer#Any'
    EXPLAINERS_URL = "https://api-onto-dev.isee4xai.com/api/explainers/list"
    response = requests.request("GET", EXPLAINERS_URL)
    explainer_list=json.loads(response.text)
    
    flag=True
    msg=""
    for exp in explainer_list:
        
        if(exp["name"]==explainer):
            
            if context["dataset_type"]!=exp["dataset_type"]:
                flag=False
                msg=msg+"\n- Dataset Type Mismatch: The model uses " + format_attr(context["dataset_type"],0,"DatasetType",trans_table) +" data but " + exp["name"] + " only supports "  + format_attr(exp["dataset_type"],0,"DatasetType",trans_table) +" data."
            
            if ANY_URI not in exp["implementation"] and context["implementation"] not in exp["implementation"]:
                flag=False
                msg=msg+"\n- Implementation Mismatch: This is a " + format_attr(context["implementation"],0,"Implementation_Framework",trans_table) +" model but " + exp["name"] + " only supports "  + format_attr(exp["implementation"],1,"Implementation_Framework",trans_table) +" implementations."
            
            if ANY_URI not in exp["ai_methods"] and len(set(context["ai_method"][0]) & set(exp["ai_methods"]))==0:
                flag=False
                msg=msg+"\n- AI Method Mismatch: The model is a " + format_attr(context["ai_method"],3,"AIMethod",trans_table) +" but " + exp["name"] + " only supports "  + format_attr(exp["ai_methods"],1,"AIMethod",trans_table) +"."
            
            if ANY_URI not in exp["ai_tasks"] and len(set(context["ai_task"]) & set(exp["ai_tasks"]))==0:
                flag=False
                msg=msg+"\n- AI Task Mismatch: "+ exp["name"] + " does not support "  + format_attr(context["ai_task"],3,"Implementation_Framework",trans_table) +" tasks."

            return flag,msg
        
    #explainer not found
    return False, "The explainer was not found."


        