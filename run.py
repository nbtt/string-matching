import load_data
import transform
import measure
import metric
import selection
import pandas as pd
from functools import reduce
from pprint import pprint
import json

import sys
import flow

pd.set_option('display.max_columns', None)
pd.set_option('max_colwidth', None)

def scenario_library(columns, create_transform_func):
    # Scenario: Library dataset, do string matching with given columns
    # Data names
    N_ACM = 'acm'
    N_DBLP = 'dblp'
    N_DBLP_ACM = flow.make_combined_name(N_DBLP, N_ACM)

    # Data paths
    file_paths = {
        N_ACM: 'data/acmProfiles',
        N_DBLP: 'data/dblpProfiles',
        N_DBLP_ACM: 'data/dblpAcmIdDuplicates'
    }

    # Transform function    
    transform_func = create_transform_func(columns)

    # Measure similarity function
    affine_gap_func = measure.affine_gap(1, 0.5, lambda char_1, char2: 2 if char_1 == char2 else -1)
    smith_waterman_func = measure.smith_waterman(2, lambda char_1, char2: 2 if char_1 == char2 else -1)

    threshold = 0.8
    min_overlap = 4

    flow.run_flow(
        file_paths,
        transform_func,
        {
            flow.F_AFFINE_GAP: affine_gap_func,
            flow.F_SMITH_WATERMAN: smith_waterman_func,
        },
        threshold,
        min_overlap
    )

def scenario_library_title():
    def create_transform_func(concat_columns):
        def inner(data_item: pd.Series):
            result = transform.concat_by_columns(concat_columns)(data_item)
            result = transform.to_lower()(result)
            result = transform.remove_non_alphanumeric_except_space()(result)
            return result
        return inner
    
    scenario_library(['title'], create_transform_func)

def scenario_library_title_authors():
    def create_transform_func(concat_columns):
        def inner(data_item: pd.Series):
            data_item_copy = data_item.copy()
            data_item_copy['authors'] = transform.sort_authors()(data_item_copy['authors'])

            result = transform.concat_by_columns(concat_columns)(data_item_copy)
            result = transform.to_lower()(result)
            result = transform.remove_non_alphanumeric_except_space()(result)
            return result
        return inner
    
    scenario_library(['title', 'authors'], create_transform_func)

def scenario_cora():
    # Scenario: Dcora dataset, do string matching with given columns
    def create_transform_func(concat_columns):
        def inner(data_item: pd.Series):
            result = transform.concat_by_columns(concat_columns)(data_item)
            result = transform.to_lower()(result)
            result = transform.remove_non_alphanumeric_except_space()(result)
            return result
        return inner
    
    # Data names
    N_CORA = 'cora'
    N_CORA_CORA = flow.make_combined_name(N_CORA, N_CORA)

    # Data paths
    file_paths = {
        N_CORA: 'data/coraProfiles',
        N_CORA_CORA: 'data/coraIdDuplicates'
    }

    # Transform function
    transform_func = create_transform_func(['title', 'year', 'pages'])

    # Measure similarity function
    affine_gap_func = measure.affine_gap(1, 0.5, lambda char_1, char2: 2 if char_1 == char2 else -1)
    smith_waterman_func = measure.smith_waterman(2, lambda char_1, char2: 2 if char_1 == char2 else -1)

    threshold = 0.8
    min_overlap = 4

    flow.run_flow(
        file_paths,
        transform_func,
        {
            flow.F_AFFINE_GAP: affine_gap_func,
            flow.F_SMITH_WATERMAN: smith_waterman_func,
        },
        threshold,
        min_overlap,
        True
    )

if __name__ == "__main__":
    scenarios = {
        "library-title": scenario_library_title,
        "library-title-authors": scenario_library_title_authors,
        "cora": scenario_cora,
    }

    if len(sys.argv) != 2 or len(sys.argv) == 2 and sys.argv[1] not in scenarios.keys():
        print(
"""Usage: python run.py <scenario_name>

Option:
\tscenario_name:
\t\t""" + "\n\t\t".join(scenarios))
        
    else:
        # Execute scenario
        scenario_name = sys.argv[1]
        scenarios[scenario_name]()