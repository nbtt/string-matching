import load_data
import transform
import measure
import pandas as pd
from functools import reduce
from pprint import pprint

def make_ground_truth_name(profile_1_name, profile_2_name):
    return profile_1_name + '_' + profile_2_name + '_gt'

# Data names
N_ACM = 'acm'
N_DBLP = 'dblp'
N_DBLP_ACM = make_ground_truth_name(N_DBLP, N_ACM)

# Data paths
file_paths = {
    N_ACM: 'data/acmProfiles',
    N_DBLP: 'data/dblpProfiles',
    N_DBLP_ACM: 'data/dblpAcmIdDuplicates'
}

# Load data
data: dict[str, pd.DataFrame] = {}
data_raw = {}
for name in file_paths:
    if name.endswith("_gt"):
        profile_names = name.split('_')[:-1]
        ground_truths, ground_truths_raw = load_data.parse_ground_truth_to_dataframe(
            file_path=file_paths[name],
            names=profile_names
        )
        data[name] = ground_truths
        data_raw[name] = ground_truths_raw
    else:
        profiles, profiles_raw = load_data.parse_entity_to_dataframe(
            file_path=file_paths[name]
        )
        data[name] = profiles
        data_raw[name] = profiles_raw

def get_profile_by_ground_truth_id(ground_truth_name, profile_name, ground_truth_id):
    return data[profile_name].loc[data[ground_truth_name].loc[ground_truth_id, profile_name],:]

print(data[N_ACM][:10], len(data[N_ACM]))
print(data[N_DBLP_ACM][:10], len(data[N_DBLP_ACM]))
print(get_profile_by_ground_truth_id(N_DBLP_ACM, N_DBLP, 0))
print(get_profile_by_ground_truth_id(N_DBLP_ACM, N_ACM, 0))

# Transform
## Columns of each data profile
for name in file_paths:
    print(name, ':\n\t', data[name].columns.to_list(), sep='')

## Transform functions
def transform_func(concat_columns):
    def inner(data_item: pd.Series):
        # may add a transform func to split authors and sort a-z and concat again
        result = transform.concat_by_columns(concat_columns)(data_item)
        # result = transform.to_lower()(result)
        # result = transform.remove_non_alphanumeric_except_space()(result)
        return result
    return inner

## Do transformation
strings: dict[str, pd.Series] = {}
dblp_acm_colunms = ['title']
dblp_acm_transform = transform_func(dblp_acm_colunms)
for name in [N_DBLP, N_ACM]:
    strings[name] = data[name].apply(dblp_acm_transform, axis=1)
pprint(strings[N_DBLP][:10].to_list())
print(type(strings[N_DBLP][0]))

# Mesaure simmilarity function
affine_gap_func = measure.affine_gap(1, 0.5, lambda char_1, char2: 2 if char_1 == char2 else -1)
smith_waterman_func = measure.smith_waterman(2, lambda char_1, char2: 2 if char_1 == char2 else -1)

def create_measure_func(string_1: str):
    def inner(data_item: str):
        return pd.Series({
            'affine_gap': affine_gap_func(string_1, data_item),
            'smith_waterman': smith_waterman_func(string_1, data_item)
        })
    return inner

result = {
    'affine_gap': [],
    'smith_waterman': []
}
measures_result = {
    'affine_gap': [],
    'smith_waterman': []
}

def create_apply_measure_func(profile_2_name, threshold):
    def inner(data_item):
        profile_1_index = data_item[1]
        profile_1_string = data_item[0]
        
        measure_func = create_measure_func(profile_1_string)
        measures = strings[profile_2_name][1340:1350].apply(measure_func)
        measures_matrix = measures.applymap(lambda measure: measure >= threshold)
        measures_index = pd.DataFrame()
        measures_index = {
            measure_name: measures_matrix.index[measures_matrix[measure_name]] for measure_name in measures_matrix
        }
        # measure_chosen = {
        #     'affine_gap': measures_matrix.index[measures_matrix['affine_gap']],
        #     'smith_waterman': measures_matrix.index[measures_matrix['smith_waterman']],
        # }

        measures_chosen = {
            measure_name: list(measures_index[measure_name].map(lambda index: [profile_1_index, index])) for measure_name in measures_index
        }

        # measures_chosen = list(measures_index['affine_gap'].map(lambda index: [profile_1_index, index]))
        # if measures_chosen is not []:
        #     result['affine_gap'].append(measures_chosen)

        for measure_name in measures_chosen:
            if len(measures_chosen[measure_name]) > 0:
                result[measure_name].append(measures_chosen[measure_name])

            measures_result[measure_name].append({
                profile_1_index: measures
            })
        
        return measures
    return inner

# Do string matching
threshold = 0.8
apply_measure_func = create_apply_measure_func(N_ACM, threshold)
strings_frame = strings[N_DBLP][1820:1830].to_frame(name='string')
strings_frame['index'] = strings_frame.index
strings_frame.apply(apply_measure_func, axis=1)

# Unpack result
result = {
    measure_name: reduce(lambda x, y: x + y, result[measure_name]) for measure_name in result
}

pprint(measures_result)
pprint(result)

# Compare with ground truth
def compute_accuracy(result, ground_truth_name):
    profile_names = ground_truth_name.split('_')[:-1]
    ground_truth = data[ground_truth_name]
    def match_indexes(indexes):
        return ((ground_truth[profile_names[0]] == indexes[0]) & (ground_truth[profile_names[1]] == indexes[1])).any()
    result_compare = {
        measure_name: list(map(match_indexes, result[measure_name])) for measure_name in result
    }
    return {
        measure_name: len(result_compare[measure_name]) / len(ground_truth.index) for measure_name in result_compare
    }, result_compare

# Acuracy
accuracy, _ = compute_accuracy(result, N_DBLP_ACM)
print(accuracy)