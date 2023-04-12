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
        result = data_item

        # make word seperated by dash into 2 words
        result = re.sub('([a-zA-Z0-9])-([a-zA-Z0-9])', '\g<1> \g<2>', result)

        # remove non-alphanumeric character except space
        result = re.sub('[^a-zA-Z0-9\s]+', '', result)

        return result
    return inner