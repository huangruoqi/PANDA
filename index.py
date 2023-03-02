import pandas as pd
def impute(df):
    from sklearn.impute import SimpleImputer
    imp_mean = SimpleImputer(strategy='mean')
    imp_mean.fit(df)
    return pd.DataFrame(imp_mean.transform(df))

n = float("nan")
df = pd.DataFrame([[1,2,3], [4, n, n], [n]*3])
print(impute(df))

