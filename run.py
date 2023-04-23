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

def scenario_library_title():
    # Scenario: Library dataset, do string matching with field title, selection by threshold
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
    def create_transform_func(concat_columns):
        def inner(data_item: pd.Series):
            # may add a transform func to split authors and sort a-z and concat again
            result = transform.concat_by_columns(concat_columns)(data_item)
            result = transform.to_lower()(result)
            result = transform.remove_non_alphanumeric_except_space()(result)
            return result
        return inner
    
    transform_func = create_transform_func(['title'])

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

def scenario_library_title_author():
    pass

def scenario_dcora():
    pass

if __name__ == "__main__":
    scenarios = {
        "library-title-threshold": scenario_library_title,
        "library-title-author": scenario_library_title_author,
        "dcora": scenario_dcora,
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