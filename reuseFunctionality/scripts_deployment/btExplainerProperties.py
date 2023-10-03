import pandas as pd
from utils import getPropertiesFormat
from utils import filter_properties

def getBTExplainerProperties(original_case):
    """
        This function is going to show the explainer properties that are in the current BT
        Petyo has to use this function to click all these properties in the form
    """
    
    return get_all_properties_from_current_bt(original_case, getPropertiesFormat())
    
    
# A function to get all the explainers in the BT, and to get all the properties that those explainers have
def get_all_properties_from_current_bt(original_case, explainer_data): 
    transformed_properties = {}
    
    nodes = original_case[0]['data']['trees'][0]['nodes']
    # print('nodes', nodes)   
       
    filtered_instances, instance_properties = {}, {}
    # Get all the explainers in the BT 
    for id, node_data in nodes.items():
        instance = node_data.get("Instance")
        # Extract "Instance" values of all IDs that start with '/'
        if instance and instance.startswith('/'):
            filtered_instances[id] = instance   
    explainer_list = list(explainer_data.keys())
    
    # Iterate through the filtered_instances
    for id, instance in filtered_instances.items():
        # print(f"ID: {id}, Instance: {instance}")
        # Find the explainer with a matching 'name' attribute
        matching_explainer = next((explainer for explainer in explainer_list if explainer == instance), None)
        #print('\nmatching_explainer', matching_explainer)
      
        # Check if a matching explainer was found
        if matching_explainer:            
            # Store the properties in the dictionary using the instance name as the key
            instance_properties[instance] = explainer_data[instance]

    # transformed_properties = filter_explainer_properties(instance_properties)
    transformed_properties = filter_properties(instance_properties, transformed_properties)
                                    
    return transformed_properties