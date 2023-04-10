
def affine_gap(c_0, c_r, c_xy):
    def inner(string_1, string_2):
        m, n = len(string_1), len(string_2)
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
        return s[m][n]
    
    return inner


affine_gap_func = affine_gap(1, 0.5, lambda char_1, char2: 2 if char_1 == char2 else -1)

affine_gap_func("Tuan Trinh", "Tuan NB Trinh")


def smith_waterman(c_g, c_xy):
    def inner(string_1, string_2):
        m, n = len(string_1), len(string_2)
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
        return s[m][n]
    return inner

smith_waterman_func = smith_waterman(2, lambda char_1, char2: 2 if char_1 == char2 else -1)

print(smith_waterman_func("Prof. John R. Smith, Univ of Wisconsin", "John R.Smith, Professor"))
    