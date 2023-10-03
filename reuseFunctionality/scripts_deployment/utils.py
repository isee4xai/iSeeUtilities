import pandas as pd
import requests 
import json
from pandas import json_normalize

PROPERTIES_FILE="properties.csv"
SIMILARITIES_FILE="similarities.csv"

MEASURES = ['common_attributes', 'weighted_ca', 'cosine', 'depth', 'detail']
PROPERTIES = {}
PROPERTIES['Explainer'] = 0
PROPERTIES['ExplainerDescription'] = 1
#PROPERTIES['ExplainabilityTechnique'] = 2
PROPERTIES['ExplainabilityTechniqueType'] = 2
PROPERTIES['DatasetType'] = 3
PROPERTIES['ExplanationOutputType'] = 4
PROPERTIES['ExplanationDescription'] = 5
PROPERTIES['Concurrentness'] = 6
PROPERTIES['Portability'] = 7
PROPERTIES['Scope'] = 8
PROPERTIES['TargetType'] = 9
PROPERTIES['OutputType'] = 10
PROPERTIES['Complexity'] = 11
PROPERTIES['AIMethodType'] = 12
PROPERTIES['AITaskType'] = 13
PROPERTIES['Backend'] = 14
PROPERTIES['metadata'] = 15

SIMPLE_PROPERTIES = [PROPERTIES['DatasetType'], PROPERTIES['Concurrentness'], PROPERTIES['Scope'], PROPERTIES['Portability'], PROPERTIES['TargetType'], PROPERTIES['Complexity']]
COMPLEX_PROPERTIES = [PROPERTIES['ExplainabilityTechniqueType'], PROPERTIES['ExplanationOutputType']]
SIMPLE_MULT_PROPERTIES = [PROPERTIES['Backend']]
COMPLEX_MULT_PROPERTIES = [PROPERTIES['OutputType'], PROPERTIES['AIMethodType'], PROPERTIES['AITaskType']]
PROP_WEIGHT = {}
PROP_WEIGHT[PROPERTIES['ExplainabilityTechniqueType']] = 0.8
PROP_WEIGHT[PROPERTIES['DatasetType']] = 1
PROP_WEIGHT[PROPERTIES['Concurrentness']] = 0.7
PROP_WEIGHT[PROPERTIES['Scope']] = 0.7
PROP_WEIGHT[PROPERTIES['Portability']] = 1
PROP_WEIGHT[PROPERTIES['TargetType']] = 1
PROP_WEIGHT[PROPERTIES['OutputType']] = 0.5
PROP_WEIGHT[PROPERTIES['ExplanationOutputType']] = 0.6
PROP_WEIGHT[PROPERTIES['Complexity']] = 0.1
PROP_WEIGHT[PROPERTIES['AIMethodType']] = 1
PROP_WEIGHT[PROPERTIES['AITaskType']] = 1
PROP_WEIGHT[PROPERTIES['Backend']] = 0.9
PROP_WEIGHT[PROPERTIES['metadata']] = 1

TOTAL_WEIGHT = 10.29999999

def isExplainer(elem):
    """
        decide if the elem is an explainer in our library
    """
    properties = pd.read_csv(PROPERTIES_FILE, delimiter=',') 
    explainers = properties["Explainer"].tolist()
    return elem in explainers

def getSimilarityValueExplainers(explainer1,explainer2):
    """
        Getting the similarity value between two explainers
    """
    matrix = pd.read_csv(SIMILARITIES_FILE, delimiter=',').set_index('explainer')
    return matrix[explainer1][explainer2]


def format_list(text, my_explainer):
    #text = text.replace('"','')
    # every explainer
    json_text = json.loads(text)
    #print(json_text)
    
    info_my_explainer = [gettingMyExplainer(json_text, my_explainer)]
    
    # API call to get the labels
    url = "https://api-onto-dev.isee4xai.com/api/onto/cockpit/ExplainerFieldsFlat"

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    json_text_label = json.loads(response.text)
    
    # API call to get the explainer hierarchy
    url = "https://api-onto-dev.isee4xai.com/api/onto/cockpit/ExplainerFields"

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    json_text_parents = json.loads(response.text)
    
    # getting the parents for complex properties
    explainability_technique_parents = getAllParents(json_text_parents['ExplainabilityTechnique']['children'])
    explanation_type_parents = getAllParents(json_text_parents['Explanation']['children'])
    presentation_parents = getAllParents(json_text_parents['InformationContentEntity']['children'])
    ai_method_parents = getAllParents(json_text_parents['AIMethod']['children'])
    ai_task_parents = getAllParents(json_text_parents['AITask']['children'])
    
    # for each explainer
    #json_list = [getLabels(x,json_text_label,json_text_parents, explainability_technique_parents, explanation_type_parents, presentation_parents, ai_method_parents, ai_task_parents) for x in json_text]
    json_list = [getLabels(x,json_text_label,json_text_parents, explainability_technique_parents, explanation_type_parents, presentation_parents, ai_method_parents, ai_task_parents) for x in info_my_explainer]
    
    df = json_normalize(json_list) 
    
    #for key,vale in json_text.items():
    df = df.drop('key', axis=1)
    df.rename(columns={'name': 'Explainer', 'explainer_description':'ExplainerDescription', 'technique': 'ExplainabilityTechniqueType', 'dataset_type':'DatasetType', 'explanation_type':'ExplanationOutputType', 'explanation_description':'ExplanationDescription', 'concurrentness':'Concurrentness','portability':'Portability','scope':'Scope','target':'TargetType','presentations':'OutputType','computational_complexity':'Complexity','ai_methods':'AIMethodType','ai_tasks':'AITaskType', 'implementation':'Backend'}, inplace=True)
    
    return df

def gettingMyExplainer(explainer_list, exp):
    """
        Function to get the explainer just added to the ontology
    """
    if explainer_list[-1]["name"]==exp:
        #print(explainer_list[-1])
        result = explainer_list[-1]
    else:
        for explainer in explainer_list:
            if explainer["name"]==exp:
                return explainer
        print("Explainer not found in the ontology")
    return result

def getLabels(elem, json_text,json_text_parents, explainability_technique_parents, explanation_type_parents, presentation_parents, ai_method_parents, ai_task_parents):
    """
        Function that retrieves the labels 
    """

    #### PARENTS
    tmp = elem["technique"]
    my_technique = json_text["ExplainabilityTechnique"][tmp]
    elem["technique"] = [my_technique] + searchParents(my_technique, explainability_technique_parents, list(), True) 
    
    
    tmp = elem["dataset_type"]
    elem["dataset_type"] = json_text["DatasetType"][tmp]
    
    #### PARENTS
    tmp = elem["explanation_type"]
    my_exp = json_text["Explanation"][tmp]
    elem["explanation_type"] = [my_exp] + searchParents(my_exp, explanation_type_parents, list(), True)
    
    tmp = elem["concurrentness"]
    elem["concurrentness"] = json_text["Concurrentness"][tmp]
    
    tmp = elem["portability"]
    elem["portability"] = json_text["Portability"][tmp]
    
    tmp = elem["scope"]
    elem["scope"] = json_text["Scope"][tmp]
    
    tmp = elem["target"]
    elem["target"] = json_text["Target"][tmp]
    
    # parents + multiple selection
    tmp = elem["presentations"]
    my_list = list()
    for e in tmp:
        label_e = json_text["InformationContentEntity"][e]
        my_list.append([label_e] + searchParents(label_e, presentation_parents, list(), True))
    elem["presentations"] = my_list
      
    tmp = elem["computational_complexity"]
    elem["computational_complexity"] = json_text["ComputationalComplexity"][tmp]
    

    tmp = elem["ai_methods"]
    my_list = list()
    for e in tmp:
        label_e = json_text["AIMethod"][e]
        my_list.append([label_e] + searchParents(label_e, ai_method_parents, list(), True))
    elem["ai_methods"] = my_list
    
    tmp = elem["ai_tasks"]
    my_list = list()
    for e in tmp:
        label_e = json_text["AITask"][e]
        my_list.append([label_e] + searchParents(label_e, ai_task_parents, list(), True))
    elem["ai_tasks"] = my_list
    
    
    # multiple selection
    tmp = elem["implementation"]
    my_list = list()
    for e in tmp:
        my_list.append(json_text["Implementation_Framework"][e])
    elem["implementation"] = my_list
    
    return elem


def getAllParents(list_parents):
    """
        Function that creates a dictionary with each parent-children. 
        If they dont have childen, the list of children is empty
    """
    my_parents = dict()
    
    for parent in list_parents:
        my_parents[parent['label']] = []
        if parent['children'] != []:
            for child in parent['children']:
                my_parents[parent['label']].append(child["label"])
            my_parents.update(getAllParents(parent['children']))
                
            
    return my_parents

def searchParents(elem, parents, my_parents, loop):
    """
        # Look for the key where the element is
        # do the same with the key until the last key doesnt appear in any children list
    """
    next_parent = getKey(elem, parents)
    if next_parent:
        my_parents = my_parents + next_parent + searchParents(next_parent[0], parents, my_parents, loop)
    else:
        loop = False
    return my_parents

def getKey(elem, parents):
    return [x for x in parents if elem in parents[x]]
    
def gettingExplainerProperties():
    """
        Function that retrieves all the explainer properties
    """
    df_fo = pd.read_csv(PROPERTIES_FILE, delimiter=',')
    return df_fo


def updateDict(my_dict):
    my_dict["explainer"] = my_dict.pop("Explainer")
    my_dict["technique"] = my_dict.pop("ExplainabilityTechniqueType")
    my_dict.pop("ExplainerDescription")
    my_dict["dataset_type"] = my_dict.pop("DatasetType")
    my_dict["explanation_type"] = my_dict.pop("ExplanationOutputType")
    my_dict.pop("ExplanationDescription")
    my_dict["concurrentness"] = my_dict.pop("Concurrentness")
    my_dict["portability"] = my_dict.pop("Portability")
    my_dict["scope"] = my_dict.pop("Scope")
    my_dict["target"] = my_dict.pop("TargetType")
    my_dict["presentations"] = my_dict.pop("OutputType")
    my_dict["computational_complexity"] = my_dict.pop("Complexity")
    my_dict["ai_methods"] = my_dict.pop("AIMethodType")
    my_dict["ai_tasks"] = my_dict.pop("AITaskType")
    my_dict["implementation"] = my_dict.pop("Backend")
    my_dict.pop("metadata")
    return my_dict   


   
def getPropertiesFormat():
    properties = gettingExplainerProperties().to_dict(orient='records')
    data_dict = {item['Explainer']: item for item in properties}
    prop_dict = {x[0]: updateDict(x[1]) for x in data_dict.items()}
    return prop_dict


## Filter the explainers and their property values
def filter_properties(properties_dict, filter_properties_dict):
    for explainer, properties in properties_dict.items():
        for prop, prop_value in properties.items(): 
            # if isinstance(prop_value, list): # isinstance() check is performed to identify if the value is a list. 
            if prop_value[1] == "[":
                property_tmp_x = prop_value[:-2].replace('[','').split('], ')
                property_tmp = [list(x.replace("'","").split(', ')) for x in property_tmp_x]
                property_flatten = [x for y in property_tmp for x in y]
                filter_properties_dict.setdefault(prop, set()).update(property_flatten)
            elif prop_value[0] == "[":
                property_tmp = prop_value.replace('[','').replace(']','').replace("'","").split(', ')
                filter_properties_dict.setdefault(prop, set()).update(property_tmp) # update() method is used to add all elements of the list to the set       
            else:
                filter_properties_dict.setdefault(prop, set()).add(prop_value)

    return filter_properties_dict
