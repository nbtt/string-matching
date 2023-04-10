import numpy as np

def edit_distance():
    def inner(string_1, string_2):
        n = len(string_1)
        m = len(string_2)
        d = np.zeros((n, m))
        for i in range(n):
            d[i, 0] = i
        for j in range(m):
            d[0, j] = j
            
        for i in range(1, n):
            for j in range(1, m):
                copy_subtitute = 0
                if string_1[i] == string_2[j]:
                    copy_subtitute = d[i - 1, j - 1] + c_xy(string_1[i], string_2[j])
                else:
                    copy_subtitute = d[i - 1, j - 1] + 1

                delete_1 = d[i - 1, j] + 1
                insert_2 = d[i, j - 1] + 1

                d[i, j] = min(copy_subtitute, delete_1, insert_2)

        result = 1 - d[n -1, m -1]/ max(n, m)
        return result
    
    return inner


affine_gap_func = affine_gap(1, 0.5, lambda char_1, char2: 2 if char_1 == char2 else -1)

affine_gap_func("Tuan Trinh", "Tuan NB Trinh")