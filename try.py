import pandas as pd

df = pd.read_csv('iskolar_ng_bayan_synthetic_dataset_v2_10000.csv')

print(df.loc[(df["ExamPassed"] == "No") & (df["ScholarshipQualified"] == "Yes")])