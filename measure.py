import pandas as pd

def affine_gap(c_0, c_r, c_xy):
    def inner(string_1, string_2):
        m, n = len(string_1), len(string_2)
        max_length = max(m, n)
        equal_char = c_xy('a','a')
        s = [[0] * (n + 1) for _ in range(m + 1)]
        M = [[0] * (n + 1) for _ in range(m + 1)]
        I_y = [[0] * (n + 1) for _ in range(m + 1)]
        I_x = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                M[i][j] = max(M[i - 1][j - 1] + c_xy(string_1[i - 1],string_2[j - 1]) , 
                                I_x[i-1][j-1] + c_xy(string_1[i - 1],string_2[j - 1]),
                                I_y[i-1][j-1] + c_xy(string_1[i - 1],string_2[j - 1]))
                I_x[i][j] = max(I_x[i - 1][j] - c_r, M[i - 1][j] - c_0 )
                I_y[i][j] = max(I_y[i][j - 1] - c_r, M[i][j - 1] - c_0 )
                s[i][j] = max(M[i][j], I_y[i][j], I_x[i][j])
        return 0 if s[m][n] <= 0 else s[m][n]/(max_length*equal_char)
    
    return inner

def smith_waterman(c_g, c_xy):
    def inner(string_1, string_2):
        m, n = len(string_1), len(string_2)
        max_length = max(m, n)
        equal_char = c_xy('a','a')
        s = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m+1):
            for j in range(1, n+1):
                score = max(
                    s[i-1][j-1] + c_xy(string_1[i-1], string_2[j-1]),
                    s[i-1][j] - c_g,
                    s[i][j-1] - c_g,
                    0
                )
                s[i][j] = score
        return s[m][n]/(max_length*equal_char)
    return inner

def create_apply_measure_func(strings, strings_sizes, strings_words, profile_2_name, threshold, measure_func_creator, select_func_creator, filter_func, inverted_indexes, result, measures_result):
    # Select function
    profile_2_strings = strings[profile_2_name]
    profile_2_sizes = strings_sizes[profile_2_name]
    profile_2_words = strings_words[profile_2_name]
    profile_2_inverted_index = inverted_indexes[profile_2_name]

    select_func = select_func_creator(
        profile_2_strings, 
        profile_2_sizes, 
        profile_2_words, 
        profile_2_inverted_index, 
        filter_func
    )
    
    def inner(data_item):
        profile_1_index = data_item[1]
        profile_1_string = data_item[0]
        
        # Measure function
        measure_func = measure_func_creator(profile_1_string)

        # select candidates
        candidates = select_func(profile_1_string)

        if (len(candidates.index) == 0):
            # No candidates
            return pd.DataFrame()

        # Calculate similarity measure
        measures = candidates.apply(measure_func)

        # Choose approriate pairs based on threshold
        measures_matrix = measures.applymap(lambda measure: measure >= threshold)
        measures_index = pd.DataFrame()
        measures_index = {
            measure_name: measures_matrix.index[measures_matrix[measure_name]] for measure_name in measures_matrix
        }

        measures_chosen = {
            measure_name: list(measures_index[measure_name].map(lambda index: [profile_1_index, index])) for measure_name in measures_index
        }

        # Save the result
        for measure_name in measures_chosen:
            if len(measures_chosen[measure_name]) > 0:
                result[measure_name].append(measures_chosen[measure_name])

            measures_result[measure_name].append({
                profile_1_index: measures
            })
        
        return measures
    return inner

if __name__ == "__main__":
    affine_gap_func = affine_gap(1, 0.5, lambda char_1, char2: 2 if char_1 == char2 else -1)
    print(affine_gap_func("Tuan Trinh", "Tuan nb Trinh"))

    smith_waterman_func = smith_waterman(1, lambda char_1, char2: 2 if char_1 == char2 else -1)
    print(smith_waterman_func("Prof. John R. Smith, Univ of Wisconsin", "John R.Smith, Professor"))
    