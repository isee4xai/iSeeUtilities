import pandas as pd
from utils import getPropertiesFormat
from utils import filter_properties


def get_all_properties_from_current_explainer(explainer):
    """
        This function returns the properties of the current explainer.
        Petyo should use this function on the form shown to include the criteria explainers when the 
        explainer reuse. The properties returned by this function have to be clicked in the form.
    """
    explainer_data = getPropertiesFormat()
    explainer_list = list(explainer_data.keys())
    result_properties, transformed_properties = {}, {}
    if explainer in explainer_list:
        result_properties[explainer] = explainer_data[explainer]
    transformed_properties = filter_properties(result_properties, transformed_properties)
                                    
    return transformed_properties