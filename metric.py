import pandas as pd

def compute_accuracy(data, prediction, ground_truth_name):
    def match_indexes(indexes):
        compare_index = ((ground_truth[profile_names[0]] == indexes[0]) & (ground_truth[profile_names[1]] == indexes[1]))
        return compare_index.any()
    
    profile_names = ground_truth_name.split('_')[:-1]
    ground_truth = data[ground_truth_name]

    prediction_compare = {
        measure_name: sum(list(map(match_indexes, prediction[measure_name]))) for measure_name in prediction
    }
    
    return {
        measure_name: prediction_compare[measure_name] / len(ground_truth.index) for measure_name in prediction_compare
    }, prediction_compare

def compute_precision_recall_f1(data, prediction_count: dict[str, int], prediction_compare: dict[str, int], ground_truth_name):
    def compute_metric(measure_name, true_positive, count_positive, count_true):
        precision = true_positive / count_positive
        recall = true_positive / count_true
        f1_score = 2 * precision * recall / (precision + recall)

        return pd.Series({'precision': precision, 'recall': recall, 'f1_score': f1_score}, name=measure_name)
    
    ground_truth = data[ground_truth_name]
    count_true = len(ground_truth)

    result = {}

    for measure_name, true_positive in prediction_compare.items():
        count_positive = prediction_count[measure_name] # number of predicted values
        
        result[measure_name] = compute_metric(measure_name, true_positive, count_positive, count_true)

    return result