import pandas as pd
import re

def concat_by_columns(columns):
    def inner(data_item: pd.Series):
        return " ".join(map(str, data_item[columns].to_list()))
    return inner

def to_lower():
    return str.lower
    
def remove_non_alphanumeric_except_space():
    def inner(data_item: str):
        return re.sub('[^a-zA-Z0-9\s]+', '', data_item)
    return inner