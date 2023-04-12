import pandas as pd

def build_inverted_index(strings: pd.Series):
    result = {}

    for index, string in strings.items():
        words = string.split(' ')
        for word in words:
            result_item = result.setdefault(word, [])
            result_item.append(index)

    return result

def build_strings_sizes_and_words(strings: pd.Series):
    def build_string(string):
        words = string[0].split(' ')
        return pd.Series([len(words), words])

    strings_sizes_and_words = strings.to_frame().apply(build_string, axis=1)
    return strings_sizes_and_words.iloc[:, 0], strings_sizes_and_words.iloc[:, 1]

def build_word_frequencies(inverted_indexes: dict[str, dict], name_1, name_2):
    word_frequencies = {}

    def build_word_frequencies_each(inverted_index):
        key = inverted_index[0]
        index = inverted_index[1]
        word_frequency = word_frequencies.setdefault(key, 0)
        word_frequencies[key] = word_frequency + len(index)
    
    for name in [name_1, name_2]:
        list(map(build_word_frequencies_each, inverted_indexes[name].items()))

    return word_frequencies

def create_sort_words_by_frequency(word_frequencies):
    def inner(words):
        result = list(set(words))
        result.sort(key=lambda word: word_frequencies[word])
        return result
    
    return inner

def create_size_filtering(threshold):
    def size_filtering(filter_info: dict):
        candidate_sizes: pd.Series = filter_info['candidate_sizes']
        size_to_filter = filter_info['size']

        min_size = size_to_filter * threshold
        max_size = size_to_filter / threshold

        def is_chosen_size(candidate_size):
            return min_size <= candidate_size <= max_size
        
        is_chosen_candidates = candidate_sizes.map(is_chosen_size)

        filtered_candidates = candidate_sizes[is_chosen_candidates]

        return filtered_candidates.index

    return size_filtering

def create_prefix_filtering(min_overlap, sort_word_func):
    def prefix_filtering(filter_info: dict):
        candidate_words: pd.Series = filter_info['candidate_words']
        words = filter_info['words']

        # create words subset to filter
        words_to_filter_size = max(0, (len(words) - min_overlap + 1))

        if words_to_filter_size == 0:
            # len(words) < min_overlap -> don't care this case
            return candidate_words.index
        
        words_to_filter = words[:words_to_filter_size]
        words_to_filter = sort_word_func(words_to_filter)

        def is_word_overlap_candidate(candidate_word):
            candidate_word_to_filter_size = max(0, (len(candidate_word) - min_overlap + 1))

            if candidate_word_to_filter_size == 0:
                return True
            
            candidate_word_to_filter = candidate_word[:candidate_word_to_filter_size]
            
            return not set(words_to_filter).isdisjoint(candidate_word_to_filter)
        
        is_chosen_candidates = candidate_words.map(is_word_overlap_candidate)

        filtered_candidates = candidate_words[is_chosen_candidates]

        return filtered_candidates.index

    return prefix_filtering