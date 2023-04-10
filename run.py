import load_data
import transform
import pandas as pd
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
dblp_acm_colunms = ['title', 'authors', 'venue', 'year']
dblp_acm_transform = transform_func(dblp_acm_colunms)
for name in [N_DBLP, N_ACM]:
    strings[name] = data[name].apply(dblp_acm_transform, axis=1)
pprint(strings[N_DBLP][:10].to_list())

# Selection function
def base_select_func(profile_2_name):
    '''select profile 2 list that might be match with profile 1'''
    def inner(profile_1_string):
        return strings[profile_2_name]
    
select = base_select_func(N_ACM)

# Mesaure simmilarity function

# Do string matching

# Compare with ground truth
