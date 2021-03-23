import datetime
import pandas as pd

col_names = ['guid','name','first', 'last', 'email' , 'value', 'date', 'phone', 'age', 'state', 'street']
csvData = pd.read_csv('/home/claire/calypso/venv/example.csv' ,names=col_names, header=None)
x = 0
for i,row in csvData.iterrows():
    x = x + 1
print(x)