import json
import requests
import copy
import numpy as np
import edist.sed as sed
from utils import isExplainer, getSimilarityValueExplainers
from applicability import applicabilityExplainer


intents = {}
intents["DEBUGGING"] = ["Is this the same outcome for similar instances?", "Is this instance a common occurrence?"]
intents["TRANSPARENCY"] = ["What is the impact of feature X on the outcome?","How does feature X impact the outcome?","What are the necessary features that guarantee this outcome?","Why does the AI system have given outcome A?","Which feature contributed to the current outcome?","How does the AI system respond to feature X?","What is the goal of the AI system?","What is the scope of the AI system capabilities?","What features does the AI system consider?","What are the important features for the AI system?", "What is the impact of feature X on the AI system?","How much evidence has been considered to build the AI system?", "How much evidence has been considered in the current outcome?","What are the possible outcomes of the AI system?","What features are used by the AI system?"] 
intents["PERFORMANCE"] = ["How confident is the AI system with the outcome?","Which instances get a similar outcome?","Which instances get outcome A?","What are the results when others use the AI System?","How accurate is the AI system?","How reliable is the AI system?","In what situations does the AI system make errors?","What are the limitations of the AI system?","In what situations is the AI system likely to be correct?"] 
intents["COMPLIANCY"] = ["How well does the AI system capture the real-world?","Why are instances A and B given different outcomes?"]
intents["COMPREHENSIBILITY"] = ["How to improve the AI system performance?","What does term X mean?","What is the overall logic of the AI system?","What kind of algorithm is used in the AI system?"]
intents["EFFECTIVENESS"] = ["What would be the outcome if features X is changed to value V?","What other instances would get the same outcome?","How does the AI system react if feature X is changed?","What is the impact of the current outcome?"] 
intents["ACTIONABILITY"] = ["What are the alternative scenarios available?","What type of instances would get a different outcome?","How can I change feature X to get the same outcome?","How to get a different outcome?","How to change the instance to get a different outcome?","How to change the instance to get outcome {outcome}?","Why does the AI system have given outcome A not B?","Which features need changed to get a different outcome?"] 

insertion_cost = 1.
deletion_cost = 1.
leave_change = 1. 
default_cost = 100

# API call to iSeeOntoAPI to get the most similar cases
def getCasesJson(treeId_paremeter,usecaseId_parameter,topK_paremeter):
    """
        Function to get the solutions for that case in json format
    """
    url = "https://api-dev.isee4xai.com/api/trees/cbr_retrieve"

    payload = json.dumps({
      "treeId": treeId_paremeter,
      "usecaseId": usecaseId_parameter,
      "topk": topK_paremeter
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    #print(response.text)

    return json.loads(response.text)


def print_node_instances(node_id, nodes_dict, node_list, id_list): 
    node = nodes_dict[node_id]
    
    node_instance = node['Instance']
    if node_instance is None:
        return None
    elif node_instance == "User Question":
        node_instance = node["params"]["Question"]["value"]
        print(typeQuestion(node_instance))
    node_list.append(node_instance)
    id_list.append(node_id)

    if 'firstChild' in node:
        first_child_id = node['firstChild']['Id']
        print_node_instances(first_child_id, nodes_dict, node_list, id_list)
        next_child = node['firstChild'].get('Next')

        while next_child is not None:
            next_child_id = next_child['Id']
            print_node_instances(next_child_id, nodes_dict, node_list, id_list)
            next_child = next_child.get('Next')

    return node_list, id_list

def get_index(node_id, nodes_dict, id_list):
    node = nodes_dict[node_id]
    node_instance = node.get('Instance')
    node_index = id_list.index(node_id)
    node_index = node_index + 1

    return node_index, node_instance

def find_parent(node_id, node, parent_child_dict, id_list, nodes_dict):
    parent_index, parent_instance = get_index(node_id, nodes_dict, id_list)
    
    if 'firstChild' in node:
        first_child_id = node['firstChild']['Id']
        child_index, child_instance = get_index(first_child_id, nodes_dict, id_list)

        if parent_index not in parent_child_dict:
            parent_child_dict[parent_index] = []
        if child_index not in parent_child_dict[parent_index]:
            parent_child_dict[parent_index].append(child_index)
        
        next_child = node['firstChild'].get('Next')
        while next_child is not None:
            next_child_id = next_child['Id']
            child_index, child_instance = get_index(next_child_id, nodes_dict, id_list)
            if child_index not in parent_child_dict[parent_index]:
                parent_child_dict[parent_index].append(child_index)  # Add child index to the parent's list
            next_child = next_child.get('Next')

        return parent_instance

def create_parent_child_dict(nodes_dict, node_list, id_list): 
    parent_child_dict = {}   
    # root = node_list[0] #r 
    parent_child_dict[0] = [1]  # Add root node with index 0

    for i, (instance, node_id) in enumerate(zip(node_list[1:], id_list), start=1):
        node_index = i
        node_id =id_list[node_index-1]
        node = nodes_dict[node_id]
        find_parent(node_id, node, parent_child_dict, id_list, nodes_dict)
    
    return parent_child_dict

def build_adjacency_list(node_list, parent_child_dict): 
    adjacency_list = [[] for _ in range(len(node_list))]

    for node_index, node_instance in enumerate(node_list):
        if node_index in parent_child_dict:
            children = parent_child_dict[node_index]
            adjacency_list[node_index] = children

    return adjacency_list

# function to translate the case solution to graph structure 
# This function must work for all the cases and the query 
# TODO
def translateCasesFromJSONtoGraph(case):
    
    tree_dict, nodes_dict, parent_child_dict = {},{},{}
    node_list = ['r'] # Added 'r' as the default root node in the node list
    id_list =[] #List of node id's 


    for idx, obj in enumerate(case, start=1):
        trees = obj['data']['trees']
        
        # Get the 'nodes' from 'trees'
        for tree in trees:
            nodes = tree.get('nodes', {})
            nodes_dict.update(nodes)
            # Get the root node
            root_node_id = tree.get('root')    

        # Call the recursive function to print node instances
        node_list, id_list= print_node_instances(root_node_id, nodes_dict, node_list = ['r'], id_list =[])
        
        # Call the function to create the parent_child dictionary
        parent_child_dict = create_parent_child_dict(nodes_dict, node_list, id_list)
        # Build the adjacency list from the behavior tree
        adjacency_list = build_adjacency_list(node_list, parent_child_dict)

        tree_key = f'tree_{idx}'
        #   tree_dict[tree_key] = trees
        tree_dict[tree_key] = {
              'tree_json': trees,
              'tree_graph': {
                  'nodes': node_list,
                  'adj': adjacency_list
              }
        }

    return tree_dict

# Remove the root and its references
def remove_root(most_similar_tree): #most_similar_tree):
    """
        Function to remove the root in the most similar BT
    """
    
    most_similar_tree_copy = copy.deepcopy(most_similar_tree) # Create a deep copy of the most similar BT 

    ## Remove the 'root' node and its connections from the JSON data
    #trees = most_similar_tree ['trees']
    # print(tree, '\n')
    
    for tree in most_similar_tree_copy:
        # Get the root node
        root_id = tree.get('root') 
        # print(root_id)
        if tree['root'] == root_id: 
            # Remove the 'root' node and its references
            del tree['nodes'][root_id] 
            del tree['root']
            break  # Assuming there is only one tree with the specified root

    # Save the modified JSON data for Substitution
    # most_similar_subtree = most_similar_tree['data']['trees'][0]['nodes']
    most_similar_subtree = most_similar_tree_copy[0]['nodes']
    
    return most_similar_subtree

# Find the parent
def get_parent_node(node_id, nodes):
#     node_dict = nodes.keys()
    for parent_node_id, node_data in nodes.items():
#         print('parent_node_id', parent_node_id)
        if "firstChild" in node_data and node_data["firstChild"]["Id"] == node_id:
            return parent_node_id
        if "Next" in node_data and node_data["Next"]["Id"] == node_id:
            return parent_node_id
    for parent_node_id, node_data in nodes.items():
        if "id" in node_data:
            parent = get_parent_node(node_id, node_data)
            if parent:
                parent = node_data['id']
                return parent
    return None

# Function to extract the IDs of children and grandchildren from selected_subtree
def extract_children_ids(node):
    child_nodes = []
    # Check if the node has a "firstChild" key
    if "firstChild" in node:
        current_node = node["firstChild"]
        # Add the first child to the list
        child_nodes.append(node["firstChild"]['Id'])
        next_child = node['firstChild'].get('Next')
        while next_child is not None:
            child_nodes.append(next_child['Id'])
            next_child = next_child.get('Next')
    return child_nodes

# # Function to recursively search and remove selected_subtree by target ID - selected composite node, their children and grandchildren 
def search_and_remove(original_tree, target_id):
    modified_tree = copy.deepcopy(original_tree)
    nodes = modified_tree['trees'][0]['nodes']
    # Check if this node's ID matches the target_id
    target_node = nodes.get(target_id)
    if target_node["id"] == target_id:
        children_ids = extract_children_ids(target_node)
        # Remove the data by deleting the node with the target_id
        del nodes[target_id]
        for child_id in children_ids:
            modified_tree = search_and_remove(modified_tree, child_id)
    return modified_tree

# Function to replace a node with a new node by ID
def substitute_node(node, target_id, new_node):
    if isinstance(node, dict):
        # Check if "Id" matches the target
        if "id" in node and node.get("id") == target_id:
            return new_node
        if "firstChild" in node:
            if node["firstChild"]["Id"] == target_id:
                node["firstChild"]["Id"] = new_node
            else:
                next_child = node['firstChild'].get('Next')
                while next_child is not None:
                    if next_child["Id"] == target_id:
                        next_child["Id"]= new_node
                    else:
                        next_child = next_child.get('Next')
    return node

# Get the modified case by substituting the most similar subtree in the original case
def get_modified_case(original_tree, selected_subtree, most_similar_subtree):
    
    """
        original_tree is the original tree where we need to remove the subtree. It is in json format
        selected_subtree should be the id of the node selected by the user
        most_similar_subtree is the tree to replace the old sub BT that the user wants to remove
    """
    
    # Find the selected composite node id 
#     for key in selected_subtree:
#         print("my_key")
#         print(key)
#         selected_composite_node = selected_subtree[key]["id"]
#     print('selected_composite_node:', selected_composite_node)
    
    # Remove the selected_composite_node, their children and grandchildren from original_case
    # for parent_id in selected_subtree.keys():
    #    modified_tree = search_and_remove(original_case, parent_id)
    #    print('\nmodified_tree:', modified_tree)
    
    # Remove the selected_composite_node, their children and grandchildren from original_case
    selected_composite_node = selected_subtree[0]['data']['trees'][0]['root']
    modified_tree = search_and_remove(original_tree[0]['data'], selected_composite_node)
    # so here, we have the tree without the tree
    
    # Find the similar composite node id
    similar_composite_node = next(iter(most_similar_subtree.keys()))
    # print('\nsimilar_composite_node:',similar_composite_node)

    # Find the parent of the selected_composite_node
    parent = get_parent_node(selected_composite_node, modified_tree['trees'][0]['nodes'])
    # print("\nParent ID:", parent)
    # parent_node = fetch_node_details(modified_tree['trees'][0]['nodes'], parent)
    parent_node = modified_tree['trees'][0]['nodes'][parent]
    
    # child_ids = extract_children_ids(parent_node)
    # print('child_ids:', child_ids)
    
    # # Substitute the target node with the new JSON structure
    # Substitute selected_composite_node with similar_composite_node
    updated_parent_node = substitute_node(parent_node, selected_composite_node, similar_composite_node)
#     print('\nupdated_parent_node', updated_parent_node)
#     print('\nmodified_tree:', modified_tree)
    
    # # Add the most_similar_subtree to the modified tree
    modified_tree['trees'][0]['nodes'].update(most_similar_subtree)
    #print('\nFinal tree:', modified_tree)

    modified_tree_final = copy.deepcopy(original_tree)
    modified_tree_final[0]['data'] = modified_tree
    
#     print("my_modified_tree")
#     print(modified_tree_final)
    
    return modified_tree

def typeQuestion(question):
    question_type = [key for key in intents.keys() if question in intents[key]]
    if question_type == []: 
        print("That question (" + question + ") is not in our catalog")
        return "NO_QUESTION"
    else:
        return question_type[0]

# delta: custom node distance function
def semantic_delta(x, y):
    #df = getSimilarityTable()
    #print(df["/Images/Anchors"]["/Images/Counterfactuals"])

    if(x==y):
        ret = 0.
    elif(x!=None and y==None): #inserting
        #print("inserting")
        ret = insertion_cost
    elif(x==None and y!=None): #deleting
        #print("deleting")
        ret = deletion_cost
    elif(x=='r'or y=='r'):  #we assign an infinite cost when comparing a root node
        #print("root")
        ret = np.inf
    elif(x in ['Sequence','Priority'] and y in['Sequence','Priority']): #if both nodes are either sequence or priority, assign null cost
        #print("sequence and priority")
        ret = 0.
    elif(x in ['Sequence','Priority'] or y in ['Sequence','Priority']): #if one of the nodes is a sequence or priority, the other won't because of the previous rule
        #print("sequence or priority")
        ret = np.inf
    elif isExplainer(x) == True and isExplainer(y) == True: # If both nodes are explainers
        ret = 1-getSimilarityValueExplainers(x,y)
    elif (isExplainer(x) == True and isExplainer(y) == False) or (isExplainer(x) == False and isExplainer(y) == True): 
        # If one node is explainer and the other one is a question
        ret = np.inf # leave_change
    elif typeQuestion(x) != "NO_QUESTION" and typeQuestion(y) != "NO_QUESTION": # here we have both question leaves
        #### Ike semantic similarity metric
        # if they are the same type
        if typeQuestion(x) == typeQuestion(y):
            ret = 0.75
        else: # if they are not the same type
            ret = 0.5
    else: # a node is not well analysed
        print("These nodes cannot be processed: " + x + " and " + y)
        return default_cost
       
    #print('sem_delta: ',str(x)," , "+str(y)+ " = "+ str(ret) )   
    return ret


def bt_sequence(tree,node,adj_node,seq):
    seq.append(node)
    if adj_node: 
        for child in adj_node:
            bt_sequence(tree, tree["nodes"][child],tree["adj"][child],seq)

# Function to calculate the edit distance between two BTs, both of them have to have graph structure
# in this case is Levenshtein edit distance
def editDistFunc(q,c,delta):
    s1=[]
    bt_sequence(q,q["nodes"][0],q["adj"][0],s1)
    s2=[]
    bt_sequence(c,c["nodes"][0],c["adj"][0],s2)
    dist = sed.sed(s1,s2,delta)
    return dist

def checkApplicabilityBT(CASE_ID, ACCESS_TOKEN, my_behaviourTree):
    """
        We get the my_behaviourTree in graph format, and check if the explainers in that BT 
    """
       
    applicability = True
    
    for node in my_behaviourTree["nodes"]:
        if node[0] == '/':
            if applicabilityExplainer(CASE_ID,ACCESS_TOKEN, node)[0] == False:
                applicability = False
                break
                
    return applicability

# MAIN
def reuseFunctionality(original_tree, queryJson, queryTree, queryCase, CASE_ID, ACCESS_TOKEN, k_cases=5, k_similar_cases=3):
    """
        original_tree -> json with the original tree  
        queryJson -> json with the sub tree to replace
        queryTree -> tree id (string)
        queryCase -> use case id (string)
        CASE_ID, ACCESS_TOKEN -> string
        k_cases -> number of similar cases we need for the retrieval query
        k_similar_cases -> number of similar similar subTrees that we need
        
        k_similar_cases cannot be greater than k_cases. If that happens, we are going to return k_cases similar cases
    """
    
    # getting the cases to compare
    my_cases = getCasesJson(queryTree,queryCase,k_cases)
            
    # getting the graph format of the solutions (trees)
    tree_dict_tmp = translateCasesFromJSONtoGraph(my_cases)
    
    # here we are checking that the similar BT is applicable
    tree_dict = dict()
    for key, value in tree_dict_tmp.items():
        if checkApplicabilityBT(CASE_ID, ACCESS_TOKEN, value['tree_graph']):
            tree_dict[key] = value
    #tree_dict = [x for x in tree_dict_tmp if checkApplicabilityBT(CASE_ID, ACCESS_TOKEN, tree_dict_tmp[x]['tree_graph'])]
    
    # trick to make the translation properly
    queryJson = [queryJson]
    # this might change when we know how we are getting the query
    tree_query = translateCasesFromJSONtoGraph(queryJson)['tree_1']['tree_graph']
    
    # for every BT in the case base:
    #   compare the query with that BT (taking into account that the query is not the same to the case)
    solution = {}
    for bt in tree_dict:
        tree_case = tree_dict[bt]['tree_graph']
        # here we make sure that the subtree is not the same that we are going to use for replacement
        if tree_query != tree_case:
            solution[bt] = editDistFunc(tree_query,tree_case,semantic_delta)    
    
    # Sort solution to get the BT with the lowest edit distance
    sorted_BTs = sorted(solution.items(), key=lambda x:x[1])
    
    # we are making sure here that we have enough similar cases
    if k_similar_cases > len(sorted_BTs):
        k_similar_cases = len(sorted_BTs)
        
    my_solutions = list()
    for similar_case in range(0,k_similar_cases):
        # getting the most similar one and the graph format of that BT
        solution_graph_format = sorted_BTs[similar_case][0]
        # From the structure above, we have to get the json format for that solution (if there is root, we have to remove the root)
        our_solution_json = tree_dict[solution_graph_format]['tree_json']
        # remove the root node from the most similar BT
        solution_no_root = remove_root(our_solution_json)
        modified_tree = get_modified_case(original_tree, queryJson, solution_no_root)
        my_solutions.append(modified_tree)
        
    return my_solutions

