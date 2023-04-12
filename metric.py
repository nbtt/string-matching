import pandas as pd

def compute_accuracy(data, prediction, ground_truth_name):
    def match_indexes(indexes):
        return ((ground_truth[profile_names[0]] == indexes[0]) & (ground_truth[profile_names[1]] == indexes[1])).any()
    
    profile_names = ground_truth_name.split('_')[:-1]
    ground_truth = data[ground_truth_name]

    prediction_compare = {
        measure_name: len(list(map(match_indexes, prediction[measure_name]))) for measure_name in prediction
    }
    
    return {
        measure_name: prediction_compare[measure_name] / len(ground_truth.index) for measure_name in prediction_compare
    }, prediction_compare

def compute_precision_recall_f1(prediction_count: dict[str, int], prediction_compare: dict[str, int], ground_truth_name):
    def compute_metric(prediction_compare_item):
        measure_name = prediction_compare_item[0]
        true_positive = prediction_compare_item[1]

        false_positive = 0

        return pd.Series({'precision': precision, 'recall': recall, 'f1_score': f1_score}, name=measure_name)
    
    profile_names = ground_truth_name.split('_')[:-1]
    ground_truth = data[ground_truth_name]
    
    return = {
        item[0]: map(compute_metric, item) for item in prediction_compare.items()
    }