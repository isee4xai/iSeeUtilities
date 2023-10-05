import pandas as pd
import json
import requests
from applicability import applicabilityExplainer

PROPERTIES_FILE="properties.csv"
SIMILARITIES_FILE="similarities.csv"


def getMostSimilarExplainer(case_id,access_token,explainer,k,property_critiques):
    """
        getting the k most similar explainer together with their similarity values
        
        getMostSimilarExplainer(explainer,k,critiques) - explainer should be a string, k an integer with the number of most similar explainer wanted. It returns the list in descending order (the most similar ones first). Critiques is the paremeter to include the critiques included by the user. If they dont include critiques, that should be {}. If they icnlude critiques, they have to include all the explainer properties in the dict, in this format: 
            
            example1 = {'technique': [], 'dataset_type': '', 'explanation_type': [], 'concurrentness': [], 'scope': [], 'portability': [], 'target': [], 'presentations': [], 'computational_complexity': [], 'ai_methods': [], 'ai_tasks': [], 'implementation': []}
            It is important to note that in the lists, we have to put the names of the properties
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
        Transforming it in json format. 
        getMostSimilarExplainerJSON(explainer,k,critiques) - It does the same than the previous one, but returning the result in json format {similar_explainer: sim_value}. Critiques is the same than before, but in this case, the parameter could not be inclided, because by default is {}
    """
    result = dict()
    
    for r in getMostSimilarExplainer(case_id,access_token,explainer,k,property_critiques):
        result[r[0]] = r[1]  
    
    
    return json.dumps(result)

def getExplainerCritiques(property_critiques):
    """
        Function to get only the explainers that share the critiques indicated by the design user
        Example of how the property_critiques format should be:
        
        example1 = {'technique': [], 'dataset_type': 'Multivariate', 'explanation_type': ["Counterfactual Explanation"], 
        'concurrentness': [], 'scope': [], 'portability': [], 'target': ['Prediction'], 'presentations': [], 
        'computational_complexity': [], 'ai_methods': [], 'ai_tasks': [], 'implementation': ['Any']}
        
        when a specific property is empty the value must be [] or [""]
        If the user does not include any property, the property_critiques should be {}
    """
    
    explainers = getPropertiesFormat()
    my_explainers = list()
    for e, value in explainers.items():
        if value["dataset_type"] == property_critiques["dataset_type"]:
            if compareListProperties(value, property_critiques):
                my_explainers.append(e)
        
    
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
    if critiques == [] or critiques == [""] or properties_explainer == ['Any'] or critiques == ['Any']:
        return True
    else:
        my_shared_elems = [x for x in critiques if x in properties_explainer]
        if my_shared_elems != []:
            return True
        else:
            return False
            return True
        else:
            return False
