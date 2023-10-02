from utils import PROPERTIES
from utils import gettingExplainerProperties

def getSimNL(explainer1, explainer2):
    explanation = ""
    formatted_df = gettingExplainerProperties()
    explainer1_atts = getRow(formatted_df, explainer1)
    explainer2_atts = getRow(formatted_df, explainer2)
    
    # print(explainer1_atts)
    
    # explanation about why they are similar
    explanation = "They are similar because "
    if explainer1_atts[PROPERTIES['DatasetType']] == explainer2_atts[PROPERTIES['DatasetType']]:
        explanation = explanation + "they can be applied to the same dataset type: " + explainer2_atts[PROPERTIES['DatasetType']] + " data, "
    if explainer1_atts[PROPERTIES['Concurrentness']] == explainer2_atts[PROPERTIES['Concurrentness']]:
        explanation = explanation + "they have the same concurrentness: " + explainer2_atts[PROPERTIES['Concurrentness']] + ", "
    if explainer1_atts[PROPERTIES['Scope']] == explainer2_atts[PROPERTIES['Scope']]:
        explanation = explanation + "they have the same scope: " + explainer2_atts[PROPERTIES['Scope']] + ", "
    if explainer1_atts[PROPERTIES['Portability']] == explainer2_atts[PROPERTIES['Portability']]:
        explanation = explanation + "they have the same portability: " + explainer2_atts[PROPERTIES['Portability']] + ", "
    if explainer1_atts[PROPERTIES['TargetType']] == explainer2_atts[PROPERTIES['TargetType']]:
        explanation = explanation + "they have the same target type: " + explainer2_atts[PROPERTIES['TargetType']] + ", "
    if explainer1_atts[PROPERTIES['Complexity']] == explainer2_atts[PROPERTIES['Complexity']]:
        explanation = explanation + "they have the same computational complexity: " + explainer2_atts[PROPERTIES['Complexity']] + ", "

    # for the complex ones, if they share one in the array, show
    # if they share more than one, show the most deep (the one in the beginning of the array)
    explanationToInclude = "they are the same explainability technique type: "
    explanation = getExplanationComplex(explainer1_atts[PROPERTIES['ExplainabilityTechniqueType']], explainer2_atts[PROPERTIES['ExplainabilityTechniqueType']], explanation, explanationToInclude)
    explanationToInclude = "they show the same explanation type: "
    explanation = getExplanationComplex(explainer1_atts[PROPERTIES['ExplanationOutputType']], explainer2_atts[PROPERTIES['ExplanationOutputType']], explanation, explanationToInclude)
    explanationToInclude = "they use the same backend: "
    explanation = getExplanationComplex(explainer1_atts[PROPERTIES['Backend']], explainer2_atts[PROPERTIES['Backend']], explanation, explanationToInclude, True)


    attributes_list = getExplanationComplexArray(explainer1_atts[PROPERTIES['OutputType']], explainer2_atts[PROPERTIES['OutputType']])
    if len(attributes_list) > 0:
        explanation = explanation + "they show the explanation with the same output type: " + ','.join(attributes_list) + ", "
    
    attributes_list = getExplanationComplexArray(explainer1_atts[PROPERTIES['AIMethodType']], explainer2_atts[PROPERTIES['AIMethodType']])
    if len(attributes_list) > 0:
        explanation = explanation + "they are applicable to the same AI method type: " + ','.join(attributes_list) + ", "
    
    attributes_list = getExplanationComplexArray(explainer1_atts[PROPERTIES['AITaskType']], explainer2_atts[PROPERTIES['AITaskType']])
    if len(attributes_list) > 0:
        explanation = explanation + "and they are applicable to the same AI task type: " + ','.join(attributes_list) + "."
    
    
    return explanation

def getRow(df, explainer):
    return df.loc[df['Explainer'] == explainer].values.flatten().tolist()

def getExplanationComplex(explainer1, explainer2, explanation_original, explanationToInclude, isBackend=False):
    
    explainer1_atts = explainer1.replace('[','').replace(']','').replace("'","").split(', ')
    explainer2_atts = explainer2.replace('[','').replace(']','').replace("'","").split(', ')
        
    common_props = [x for x in explainer1_atts if x in explainer2_atts]
    common_props_len = len(common_props)
    if common_props_len > 0:
        if isBackend==False:
            explanation_original = explanation_original + explanationToInclude + common_props[0] + ", "
        else:
            explanation_original = explanation_original + explanationToInclude + ','.join(common_props) + ", "
    return explanation_original

def getExplanationComplexArray(explainer1, explainer2):
    explainer1_tmp_x = explainer1[:-2].replace('[','').split('], ')
    explainer1_atts = [list(x.replace("'","").split(', ')) for x in explainer1_tmp_x]

    explainer2_tmp_x = explainer2[:-2].replace('[','').split('], ')
    explainer2_atts = [list(x.replace("'","").split(', ')) for x in explainer2_tmp_x]
    
    attributes_list = list()
    for attrib_list1 in explainer1_atts:
        for attrib_list2 in explainer2_atts:
            common_props = [x for x in attrib_list1 if x in attrib_list2]
            common_props_len = len(common_props)
            if common_props_len > 0:
                attributes_list.append(common_props[0])
                
    return list(set(attributes_list))

