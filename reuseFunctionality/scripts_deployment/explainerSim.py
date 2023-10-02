import pandas as pd
import json
import requests
from applicability import applicabilityExplainer

PROPERTIES_FILE="properties.csv"
SIMILARITIES_FILE="similarities.csv"



def getMostSimilarExplainer(case_id,access_token,explainer,k,property_critiques):
    """
        getting the k most similar explainer together with their similarity values
    """
    matrix = pd.read_csv(SIMILARITIES_FILE, delimiter=',').set_index('explainer')
    
    # here get only the explainers that have the properties in property_critiques
    if property_critiques != {}: # this measn the user has included critiques
        # get all the explainers
        explainers_critiques = getExplainerCritiques(property_critiques) 
        # filter matrix
        matrix = matrix.loc[explainers_critiques]
    
    
    my_explainer = matrix[explainer]
    
    explainer_values_sim = my_explainer.tolist()
    explainer_list = my_explainer.index.tolist()
    # check applicability of every explainer
    matrix_explainer = [(explainer_list[i], explainer_values_sim[i]) for i in range(len(explainer_values_sim)) if ((explainer_values_sim[i] != 0) and (applicabilityExplainer(case_id,access_token, explainer_list[i])[0] != False))]
       
    matrix_explainer_sorted = sorted(matrix_explainer, key=lambda x: x[1], reverse=True)
       
    return matrix_explainer_sorted[1:k+1]

def getMostSimilarExplainerJSON(case_id,access_token,explainer,k,property_critiques={}):
    """
        Transforming it in json format
    """
    result = dict()
    
    for r in getMostSimilarExplainer(case_id,access_token,explainer,k,property_critiques):
        result[r[0]] = r[1]  
    
    
    return json.dumps(result)

def getExplainerCritiques(property_critiques):
    """
        Function to get only the explainers that share the critiques indicated by the design user
    """
    # get all the properties for all the explainers
    url = "https://api-onto-dev.isee4xai.com/api/explainers/list"
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    explainers = json.loads(response.text)
    
    my_explainers = list()
    for e in explainers:
        if e["dataset_type"] == property_critiques["dataset_type"]:
            if compareListProperties(e, property_critiques):
                my_explainers.append(e["name"])
        
    
    # get only the explainers that includes the critiques (from PROPERTIES_FILE)
    return my_explainers

def compareListProperties(e1, e2):
    """
        Function to know if two explainers share properties (in lists)
        e2 is the critique - then, if the properties in e2 are in e1, we can get the explainer
    """
    explainersEquals = False
    if critiqueIsInExplainer(e2["technique"], e1["technique"]) and critiqueIsInExplainer(e2["explanation_type"], e1["explanation_type"]) and critiqueIsInExplainer(e2["concurrentness"], e1["concurrentness"]) and critiqueIsInExplainer(e2["portability"], e1["portability"]) and critiqueIsInExplainer(e2["scope"], e1["scope"]) and critiqueIsInExplainer(e2["target"], e1["target"]) and critiqueIsInExplainer(e2["computational_complexity"], e1["computational_complexity"]) and critiqueIsInExplainer(e2["presentations"], e1["presentations"]) and critiqueIsInExplainer(e2["ai_methods"], e1["ai_methods"]) and critiqueIsInExplainer(e2["ai_tasks"], e1["ai_tasks"]) and critiqueIsInExplainer(e2["implementation"], e1["implementation"]):
        return True

def critiqueIsInExplainer(critiques, properties_explainer):
    # If the property list is empty (or any for implementation), that explainer can be still on the list
    if critiques == [] or critiques == ['http://www.w3id.org/iSeeOnto/explainer#Any']:
        return True
    else:
        my_shared_elems = [x for x in critiques if x in properties_explainer]
        if my_shared_elems != []:
            return True
        else:
            return False