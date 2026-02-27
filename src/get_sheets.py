import pandas as pd
import requests

url = "https://github.com/AIOE-Data/AIOE/raw/main/AIOE_DataAppendix.xlsx"
print(f"Loading {url}")
xl = pd.ExcelFile(url)
print("Sheet names:", xl.sheet_names)

for sheet in xl.sheet_names:
    if sheet == 'Appendix A':
        df = xl.parse(sheet)
        print(f"\nSheet: {sheet}")
        print("Columns:", df.columns.tolist())
        print(df.head(3))
        break
