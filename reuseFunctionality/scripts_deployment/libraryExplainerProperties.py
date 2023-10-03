import pandas as pd
from utils import getPropertiesFormat
from utils import filter_properties


def getLibraryExplainerProperties():
    """
        This function returns all the properties for the explainers that we have in the explainer library
    """
    return filter_properties(getPropertiesFormat(), {})