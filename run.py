import load_data
import transform
import measure
import metric
import selection
import pandas as pd
from functools import reduce
from pprint import pprint
import json

def make_combined_name(profile_1_name, profile_2_name, postfix='_gt'):
    return profile_1_name + '_' + profile_2_name + postfix

# Data names
N_ACM = 'acm'
N_DBLP = 'dblp'
N_DBLP_ACM = make_combined_name(N_DBLP, N_ACM)

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
        result = transform.to_lower()(result)
        result = transform.remove_non_alphanumeric_except_space()(result)
        return result
    return inner

# Selection
def create_inverted_indexes(strings, names):
    def build_inverted_indexes(name):
        return selection.build_inverted_index(strings[name])

    inverted_indexes = list(map(build_inverted_indexes, names))
    return {
        names[i]: inverted_index for i, inverted_index in enumerate(inverted_indexes)
    }

def create_select_func(profile_2_data, profile_2_sizes, profile_2_words, inverted_indexes: dict, filter_func):
    def inner(profile_1_string):
        profile_1_words = profile_1_string.split(' ')
        profile_1_size = len(profile_1_words)
        profile_2_indexes = []

        for word in profile_1_words:
            profile_2_indexes_by_word = inverted_indexes.setdefault(word, [])
            profile_2_indexes += profile_2_indexes_by_word

        profile_2_indexes = list(set(profile_2_indexes))
        print("before", len(profile_2_indexes))

        candidate_sizes = profile_2_sizes[profile_2_indexes]
        profile_2_indexes_chosen = filter_func({
            'candidate_sizes': candidate_sizes, 
            'size': profile_1_size,
            'candidate_words': profile_2_words,
            'words': profile_1_words,
        })
        print("after", len(profile_2_indexes_chosen))

        return profile_2_data[profile_2_indexes_chosen]

    return inner

# Do transformation & selection & inverted index
strings: dict[str, pd.Series] = {}
strings_sizes: dict[str, pd.Series] = {}
strings_words: dict[str, pd.Series] = {}

dblp_acm_colunms = ['title']
dblp_acm_transform = transform_func(dblp_acm_colunms)
for name in [N_DBLP, N_ACM]:
    strings[name] = data[name].apply(dblp_acm_transform, axis=1)
    strings_sizes[name], strings_words[name] = selection.build_strings_sizes_and_words(strings[name])

pprint(strings[N_DBLP][:10].to_list())

inverted_indexes = create_inverted_indexes(strings, [N_DBLP, N_ACM])
# print(inverted_indexes)

## Save inverted index
with open("export/inverted_index.json", "w") as f:
    json.dump(inverted_indexes, f, indent=4)

# Word frequencies
word_frequencies = {}

for name_pair in [[N_DBLP, N_ACM]]:
    name = make_combined_name(*name_pair, "")
    word_frequencies[name] = selection.build_word_frequencies(inverted_indexes, *name_pair)

## List of functions to sort word by frequency
sort_word_by_frequencies = {
    name: selection.create_sort_words_by_frequency(word_frequencies[name]) for name in word_frequencies
}

for name_pair in [[N_DBLP, N_ACM]]:
    name = make_combined_name(*name_pair, "")
    for single_name in name_pair:
        strings_words[single_name] = strings_words[single_name].map(sort_word_by_frequencies[name])

print(word_frequencies)
print(strings_words)

## Save word frequencies
with open("export/word_frequencies.json", "w") as f:
    json.dump(word_frequencies, f, indent=4)

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

prediction = {
    'affine_gap': [],
    'smith_waterman': []
}
measures_prediction = {
    'affine_gap': [],
    'smith_waterman': []
}

# Do string matching
threshold = 0.8
min_overlap = 4

size_filtering = selection.create_size_filtering(threshold)
prefix_filtering = selection.create_prefix_filtering(
    min_overlap, 
    sort_word_by_frequencies[make_combined_name(N_DBLP, N_ACM, "")]
)

def filter_func(filter_info):
    filtered_indexes = size_filtering(filter_info)
    print("after size filtering", len(filtered_indexes))

    # update filtered information
    filter_info['candidate_words'] = filter_info['candidate_words'][filtered_indexes]

    filtered_indexes = prefix_filtering(filter_info)

    return filtered_indexes

apply_measure_func = measure.create_apply_measure_func(
    strings,
    strings_sizes,
    strings_words,
    N_ACM,
    threshold, 
    create_measure_func, 
    create_select_func,
    filter_func,
    inverted_indexes,
    prediction, 
    measures_prediction
)
strings_frame = strings[N_DBLP][:10].to_frame(name='string')
strings_frame['index'] = strings_frame.index
strings_frame.apply(apply_measure_func, axis=1)

# Unpack result
prediction = { measure_name: reduce(lambda x, y: x + y, prediction[measure_name]) for measure_name in prediction }

# pprint(measures_result)
prediction_count = {
    measure_name: len(prediction[measure_name]) for measure_name in prediction
}
pprint(prediction_count)

# Acuracy
acurracy, prediction_compare = metric.compute_accuracy(data, prediction, N_DBLP_ACM)
print(prediction_compare)
print(acurracy)