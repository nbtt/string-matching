import load_data
import transform
import measure
import metric
import selection
import pandas as pd
from functools import reduce
from pprint import pprint
import json
import os

P_EXPORT = "export" # Export folder
F_AFFINE_GAP = "affine_gap"
F_SMITH_WATERMAN = "smith_waterman"

def make_combined_name(profile_1_name, profile_2_name, postfix='_gt'):
    return profile_1_name + '_' + profile_2_name + postfix

def run_flow(
        file_paths, # path to data files
        transform_func, # transform function to transform data item to string
        measure_func, # measure function to calculate simmilarity between 2 strings
        threshold, # threshold of similarity to choose matched pair
        min_overlap, # minimum number of overlapping words in 2 strings in prefix filtering
        isDirtyER = False, # indicates if given data is for Dirty ER problem instead of Clean-Clean ER problem
        export_prefix = "", # export file prefix
    ):
    profile_names = []
    ground_truth_name = None
    affine_gap_func = measure_func[F_AFFINE_GAP]
    smith_waterman_func = measure_func[F_SMITH_WATERMAN]

    # Load data
    data: dict[str, pd.DataFrame] = {}
    data_raw = {}
    for name in file_paths:
        if name.endswith("_gt"):
            # Set ground truth name & profile names
            ground_truth_name = name
            profile_names = name.split('_')[:-1]
            if isDirtyER:
                profile_names[0] += ".1"
                profile_names[1] += ".2"
                ground_truth_name = profile_names[0] + "_" + profile_names[1] + "_gt"
            
            # Load ground truth data
            ground_truths, ground_truths_raw = load_data.parse_ground_truth_to_dataframe(
                file_path=file_paths[name],
                names=profile_names
            )
            data[ground_truth_name] = ground_truths
            data_raw[ground_truth_name] = ground_truths_raw
        else:
            # Load entity data
            profiles, profiles_raw = load_data.parse_entity_to_dataframe(
                file_path=file_paths[name]
            )
            if isDirtyER:
                data[name + ".1"] = profiles
                data_raw[name + ".1"] = profiles_raw

                data[name + ".2"] = profiles
                data_raw[name + ".2"] = profiles_raw
            else:
                data[name] = profiles
                data_raw[name] = profiles_raw

    def get_profile_by_ground_truth_id(ground_truth_name, profile_name, ground_truth_id):
        return data[profile_name].loc[data[ground_truth_name].loc[ground_truth_id, profile_name],:]

    # Constant
    combined_name = make_combined_name(*profile_names, "")
    P_INVERTED_INDEX = os.path.join(P_EXPORT, combined_name + "_inverted_index.json")
    P_WORD_FREQS = os.path.join(P_EXPORT, combined_name + "_word_frequencies.json")
    if len(export_prefix) > 0:
        P_INVERTED_INDEX = os.path.join(P_EXPORT, export_prefix + "_inverted_index.json")
        P_WORD_FREQS = os.path.join(P_EXPORT, export_prefix + "_word_frequencies.json")

    def make_html_name(name, post_fix):
        if len(export_prefix) > 0:
            return os.path.join(P_EXPORT, export_prefix + "_" + name + "_" + post_fix + ".html")
        return os.path.join(P_EXPORT, combined_name + "_" + name + "_" + post_fix + ".html")

    print("Data:")
    P_DATA_0 = make_html_name("data", profile_names[0])
    print(profile_names[0], ':\n', data[profile_names[0]], sep='')
    data[profile_names[0]].to_html(P_DATA_0)
    if not isDirtyER:
        P_DATA_1 = make_html_name("data", profile_names[1])
        print(profile_names[1], ':\n', data[profile_names[1]], sep='')
        data[profile_names[1]].to_html(P_DATA_1)
    print(ground_truth_name, ':\n', data[ground_truth_name], sep='')
    P_DATA_GT = make_html_name("data", "gt")
    data[ground_truth_name].to_html(P_DATA_GT)
    print("\nFirst matched profiles:")
    print(profile_names[0], ':\n', get_profile_by_ground_truth_id(ground_truth_name, profile_names[0], 0), sep='')
    print(profile_names[1], ':\n', get_profile_by_ground_truth_id(ground_truth_name, profile_names[1], 0), sep='')

    # Transform
    ## Columns of each data profile
    print("\nColumns:")
    for name in data.keys():
        print(name, ':\n\t', data[name].columns.to_list(), sep='')

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
            # print("before select", len(profile_2_indexes))

            candidate_sizes = profile_2_sizes[profile_2_indexes]
            profile_2_indexes_chosen = filter_func({
                'candidate_sizes': candidate_sizes, 
                'size': profile_1_size,
                'candidate_words': profile_2_words,
                'words': profile_1_words,
            })
            # print("after select", len(profile_2_indexes_chosen))

            return profile_2_data[profile_2_indexes_chosen]

        return inner

    # Do transformation & selection & inverted index
    strings: dict[str, pd.Series] = {}
    strings_sizes: dict[str, pd.Series] = {}
    strings_words: dict[str, pd.Series] = {}

    for name in profile_names:
        strings[name] = data[name].apply(transform_func, axis=1)
        strings_sizes[name], strings_words[name] = selection.build_strings_sizes_and_words(strings[name])

    print("\nTransformed strings:")
    print(profile_names[0], ':', sep='')
    pprint(strings[profile_names[0]][:10].to_list())
    P_TRANSFORM_0 = make_html_name("transform", profile_names[0])
    strings[profile_names[0]].to_frame(profile_names[0]).to_html(P_TRANSFORM_0)
    P_TRANSFORM_1 = make_html_name("transform", profile_names[1])
    strings[profile_names[1]].to_frame(profile_names[1]).to_html(P_TRANSFORM_1)

    inverted_indexes = create_inverted_indexes(strings, profile_names)
    # print(inverted_indexes)

    ## Save inverted index
    with open(P_INVERTED_INDEX, "w") as f:
        json.dump(inverted_indexes, f, indent=4)

    # Word frequencies
    word_frequencies = {}
    word_frequencies[combined_name] = selection.build_word_frequencies(inverted_indexes, *profile_names)

    ## List of functions to sort word by frequency
    sort_word_by_frequencies = {
        name: selection.create_sort_words_by_frequency(word_frequencies[name]) for name in word_frequencies
    }
    
    for profile_name in profile_names:
        strings_words[profile_name] = strings_words[profile_name].map(sort_word_by_frequencies[combined_name])

    # print(word_frequencies)
    print("\nSort word in strings by frequencies:")
    print(profile_names[0], ':\n', strings_words[profile_names[0]], sep='')
    P_SORTED_0 = make_html_name("sorted", profile_names[0])
    strings_words[profile_names[0]].to_frame(name=profile_names[0]).to_html(P_SORTED_0)
    if not isDirtyER:
        print(profile_names[1], ':\n', strings_words[profile_names[1]], sep='')
        P_SORTED_1 = make_html_name("sorted", profile_names[1])
        strings_words[profile_names[1]].to_frame(name=profile_names[1]).to_html(P_SORTED_1)

    ## Save word frequencies
    with open(P_WORD_FREQS, "w") as f:
        json.dump(word_frequencies, f, indent=4)

    # Mesaure simmilarity creator
    def create_measure_func(string_1: str):
        def inner(data_item: str):
            return pd.Series({
                F_AFFINE_GAP: affine_gap_func(string_1, data_item),
                F_SMITH_WATERMAN: smith_waterman_func(string_1, data_item)
            })
        return inner

    prediction = {
        F_AFFINE_GAP: [],
        F_SMITH_WATERMAN: []
    }
    measures_prediction = {
        F_AFFINE_GAP: [],
        F_SMITH_WATERMAN: []
    }

    # Do string matching
    size_filtering = selection.create_size_filtering(threshold)
    prefix_filtering = selection.create_prefix_filtering(
        min_overlap, 
        sort_word_by_frequencies[combined_name]
    )

    def filter_func(filter_info):
        filtered_indexes = size_filtering(filter_info)
        # print("after size filtering", len(filtered_indexes))

        # update filtered information
        filter_info['candidate_words'] = filter_info['candidate_words'][filtered_indexes]

        filtered_indexes = prefix_filtering(filter_info)

        return filtered_indexes

    apply_measure_func = measure.create_apply_measure_func(
        strings,
        strings_sizes,
        strings_words,
        profile_names[1],
        threshold, 
        create_measure_func, 
        create_select_func,
        filter_func,
        inverted_indexes,
        prediction, 
        measures_prediction
    )
    strings_frame = strings[profile_names[0]][:10].to_frame(name='string')
    strings_frame['index'] = strings_frame.index
    strings_frame.apply(apply_measure_func, axis=1)

    # Unpack result
    prediction = { measure_name: reduce(lambda x, y: x + y, prediction[measure_name]) for measure_name in prediction }

    # pprint(measures_result)
    prediction_count = {
        measure_name: len(prediction[measure_name]) for measure_name in prediction
    }
    print("\nPrediction count:")
    pprint(prediction_count)

    # Metric
    prediction_compare = metric.compare_prediction(data, prediction, ground_truth_name)

    metric_result = metric.compute_precision_recall_f1(data, prediction_count, prediction_compare, ground_truth_name)

    print("\nPrediction true positive:")
    print(prediction_compare)
    print("\nPrecision, recall & F1 score:")
    for measure_name in metric_result.keys():
        print("\n", measure_name, ":\n", metric_result[measure_name], sep='')