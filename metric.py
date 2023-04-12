def compute_accuracy(data, result, ground_truth_name):
    def match_indexes(indexes):
        return ((ground_truth[profile_names[0]] == indexes[0]) & (ground_truth[profile_names[1]] == indexes[1])).any()
    
    profile_names = ground_truth_name.split('_')[:-1]
    ground_truth = data[ground_truth_name]

    result_compare = {
        measure_name: len(list(map(match_indexes, result[measure_name]))) for measure_name in result
    }
    
    return {
        measure_name: result_compare[measure_name] / len(ground_truth.index) for measure_name in result_compare
    }, result_compare