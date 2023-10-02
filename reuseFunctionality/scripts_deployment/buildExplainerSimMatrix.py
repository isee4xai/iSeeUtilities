import pandas as pd
import requests
from utils import format_list
from utils import PROPERTIES_FILE, SIMILARITIES_FILE,MEASURES,PROPERTIES,PROP_WEIGHT, TOTAL_WEIGHT, SIMPLE_PROPERTIES, COMPLEX_PROPERTIES, COMPLEX_MULT_PROPERTIES, SIMPLE_MULT_PROPERTIES



def updateExplainerSimilarities(explainer_name):
    """
        Function to be called when creating a new explainer
    """
    
    # Getting explainer
    url = "https://api-onto-dev.isee4xai.com/api/explainers/list"
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    df_explainer = format_list(response.text, explainer_name)
    
    # update csv with properties
    properties = pd.read_csv(PROPERTIES_FILE, delimiter=',') 
    
    dataframes = [properties, df_explainer]
    df_fo = pd.concat(dataframes)
    
    #print(df_fo)
    
    # PROPERTIES_FILE
    df_fo.to_csv(PROPERTIES_FILE,index=False)
    # trick to make the new explainer reading works when calculating the similarities
    df_fo = pd.read_csv(PROPERTIES_FILE, delimiter=',') 
    
    # update csv with similarities
    # similarities = pd.read_csv('similarities_updated.csv') 
    
    # get all the explainers already in the dataframe similarities + new explainer
    explainers = df_fo["Explainer"].tolist()
    #all_explainers = explainers + [explainer_name]
    
    # create the similarities + create the dataframe 
    matrix = build_matrix(df_fo, explainers) #, explainer_name) #all_explainers
    
    # concat the old df and the new df
    #result = pd.concat([similarities, matrix.reset_index()])
        
#     new_explainer = [float('nan')] * len(explainers) 
    
#     result["prueba"] = new_explainer + [1.0]
#     result["prueba2"] = new_explainer + [1.0]
    # save the new dataframe in the similarities.csv
    
    # SIMILARITIES_FILE
    matrix.reset_index().to_csv(SIMILARITIES_FILE,index=False)
    
    return


def build_matrix(df_data, explainers): #, e1):
    """ This function receives the dataframe with all the data of all the explainers and the list of the explainers"""
    
    #for measure in MEASURES:
    data = [] 
    for e1 in explainers:
        for e2 in explainers:
            e1_data = list(df_data.loc[df_data['Explainer'].isin([e1])].iloc[0])
            e2_data = list(df_data.loc[df_data['Explainer'].isin([e2])].iloc[0])

            sim = apply_measure(e1_data, e2_data, MEASURES[3]) # measure
            data.append({'explainer': e1, 'e2': e2, 'sim': sim})

    sim_matrix = pd.DataFrame(data)    
    matrix = sim_matrix.pivot(index='explainer', columns='e2', values='sim')
    matrix = matrix.fillna(0) 
    
    return matrix

def apply_measure(e1, e2, measure):
     
    """
        Function that returns similarity value with the measure
        
    """
    
    # apply similarity measure to those explainers
    if measure == 'common_attributes':
        sim_result = apply_common_attributes(e1, e2)
    elif measure == 'weighted_ca':
        sim_result = apply_weighted_ca(e1, e2)
    elif measure == 'cosine':
        sim_result = apply_cosine(e1, e2)
    elif measure == 'depth':
        sim_result = appy_depth(e1, e2)
    elif measure == 'detail':
        sim_result = appy_detail(e1, e2)
    
        
    return sim_result

def apply_common_attributes(explainer1, explainer2):
    """ Function that calculates the similarity between two explainers considering the number of attributes shared """
    #print(explainer1)
    #print(explainer2)
    
    count = 0
    if explainer1[PROPERTIES['Explainer']] == explainer2[PROPERTIES['Explainer']]: # if the explainer is the same
        return 1
    elif explainer1[PROPERTIES['ExplainabilityTechniqueType']] == explainer2[PROPERTIES['ExplainabilityTechniqueType']]: # if the explainability technique is the same
        return 0.9
    elif explainer1[PROPERTIES['DatasetType']] != explainer2[PROPERTIES['DatasetType']]:
        return count
    else:
        i = 2
        while i < len(explainer1):
            if explainer1[i] == explainer2[i]:
                count = count + 1
            i = i + 1

        return count/len(explainer1)

def apply_weighted_ca(explainer1, explainer2):
    """ 
        Function that calculates the similarity between two explainers considering the number of attributes shared. 
        Each attribute has a weight
    """
    count = 0
    if explainer1[PROPERTIES['Explainer']] == explainer2[PROPERTIES['Explainer']]:
        return 1
    elif explainer1[PROPERTIES['ExplainabilityTechniqueType']] == explainer2[PROPERTIES['ExplainabilityTechniqueType']]: # if the explainability technique is the same
        return 0.9
    elif explainer1[PROPERTIES['DatasetType']] != explainer2[PROPERTIES['DatasetType']]:
        return count    
    else:
        i = 2
        while i < len(explainer1):
            if explainer1[i] == explainer2[i]:
                count = count + PROP_WEIGHT[i]
            i = i + 1

        return count/TOTAL_WEIGHT 

def get_parent_cosine(e1_parents, e2_parents):
    """
        it return a weight proportional to the parents the explainers share
    """
    if e1_parents == e2_parents:
        
        return 1
    else:
        
        shared = [x for x in e1_parents if x in e2_parents]
        
        return len(shared) / len(set(e1_parents + e2_parents))

def get_parent_depth(e1_parents, e2_parents):
    """
        it returns a weight according to the deep measure: 
        max depth of shared parents (expl1, expl2) / max(depth(expl1), depth(expl2))
    """
    if e1_parents == e2_parents:
        
        return 1
    else:
        
        LCS = len([x for x in e1_parents if x in e2_parents])
        
        denominator = max([len(e1_parents), len(e2_parents)])
        
        if denominator == 0 or LCS == 0:
            return 0
        else:
            
            return (LCS)/denominator 

def get_parent_detail(e1_parents, e2_parents):
    """
        it returns a weight according to the detail measure: 
        detail = 1 - (1 / 2*(len(explain1) + len(explain2))
    """
    if e1_parents == e2_parents:
        return 1
    else:
        return 1 - (1 / (2*(len(e1_parents) + len(e2_parents))))


def weight_onto(pos, e1_parents, e2_parents, measure):
    """ Returns the weight for each attribute """

    if measure == "cosine":
        return PROP_WEIGHT[pos] * get_parent_cosine(e1_parents, e2_parents)
    elif measure == "depth":
        return PROP_WEIGHT[pos] * get_parent_depth(e1_parents, e2_parents)
    elif measure == "detail":
        return PROP_WEIGHT[pos] * get_parent_detail(e1_parents, e2_parents)

def appy_measure_parents(explainer1, explainer2, measure):
    """
        Auxiliar function to apply similarity metrics
    """
    
    count = 0
    if explainer1[PROPERTIES['Explainer']] == explainer2[PROPERTIES['Explainer']]:
        return 1
    elif explainer1[PROPERTIES['ExplainabilityTechniqueType']] == explainer2[PROPERTIES['ExplainabilityTechniqueType']]: # if the explainability technique is the same
        return 0.9
    elif explainer1[PROPERTIES['DatasetType']] != explainer2[PROPERTIES['DatasetType']]:
        return count
    else:
        i = 2
        while i < len(explainer1):
            if i in SIMPLE_PROPERTIES:
                if explainer1[i] == explainer2[i]:
                    count = count + PROP_WEIGHT[i]
            elif i in COMPLEX_PROPERTIES:
                explainer1_tmp = explainer1[i].replace('[','').replace(']','').replace("'","").split(', ')
                explainer2_tmp = explainer2[i].replace('[','').replace(']','').replace("'","").split(', ')
                count = count + weight_onto(i, explainer1_tmp, explainer2_tmp, measure)
            elif i in SIMPLE_MULT_PROPERTIES:
                # transform the string in a list and for each value, do the same we have in simple_properties
                explainer1_tmp = explainer1[i].replace('[','').replace(']','').replace("'","").split(', ')
                explainer2_tmp = explainer2[i].replace('[','').replace(']','').replace("'","").split(', ')
                
                if explainer1_tmp == ['Any'] or explainer2_tmp == ['Any']:
                    count = count + (PROP_WEIGHT[i])
                else:
                    common_props = len([x for x in explainer1_tmp if x in explainer2_tmp]) 
                    union_props_tmp = [x for x in explainer2_tmp if x not in explainer1_tmp]
                    union_props_tmp = union_props_tmp + explainer1_tmp
                    union_props = len(union_props_tmp)

                if common_props != 0:
                    count = count + (PROP_WEIGHT[i] * (common_props/union_props))
            elif i in COMPLEX_MULT_PROPERTIES:
                # transform the string in a list and for each value, do the same we have in complex properties
                explainer1_tmp_x = explainer1[i][:-2].replace('[','').split('], ')
                explainer1_tmp = [list(x.replace("'","").split(', ')) for x in explainer1_tmp_x]
                
                explainer2_tmp_x = explainer2[i][:-2].replace('[','').split('], ')
                explainer2_tmp = [list(x.replace("'","").split(', ')) for x in explainer2_tmp_x]

                common_props = len([x for x in explainer1_tmp if x in explainer2_tmp]) 
                union_props_tmp = [x for x in explainer2_tmp if x not in explainer1_tmp]
                union_props_tmp = union_props_tmp + explainer1_tmp
                union_props = len(union_props_tmp)
                
                weight_complex = 0
                indx = True
                for j in explainer1_tmp:
                    for k in explainer2_tmp:
                        weigth_tmp = (weight_onto(i, j, k, measure) * (common_props/union_props))
                        
                        if weigth_tmp != 0:
                            if indx:
                                weight_complex = weigth_tmp
                                indx = False
                            else:
                                weight_complex = weight_complex * weigth_tmp
                            
                count = count + weight_complex
            
            
            
            i = i + 1
        
        # print(count)
        return count/TOTAL_WEIGHT #len(explainer1) 

def apply_cosine(explainer1, explainer2):
    """
        Function that calculates the similarity between two explainers considering the number of attributes shared. 
        Each attribute has a weight. Furthermore, we consider if the nodes are the same for the concepts 
        ExplanationType, ExplainabilityTechniqueType, Information Content Entity, AI MEthod, AI task.
        If they are not, we look into their parent nodes in the ontology 
    """
    return appy_measure_parents(explainer1, explainer2, "cosine")

def appy_depth(explainer1, explainer2):
    """
        Function that calculates the similarity between two explainers. In this case the concepts 
        ExplanationType, ExplainabilityTechniqueType, Information Content Entity, AI MEthod, AI task
        are used to measure the depth of these concepts which is going to contribute to get the similarity value
    """
    return appy_measure_parents(explainer1, explainer2, "depth")

def appy_detail(explainer1, explainer2):
    """
        Function that calculates the similarity between two explainers with detail function for 
        ExplanationType, ExplainabilityTechniqueType, Information Content Entity, AI MEthod, AI task
        detail = 1 - (1 / 2*(len(explain1) + len(explain2))
    """
    return appy_measure_parents(explainer1, explainer2, "detail")