from flask import Flask, render_template, request, redirect, url_for, make_response, send_file, flash
import os
from os.path import join, dirname, realpath
import pandas as pd
from pandas import DataFrame
import mysql.connector
import datetime
import csv
from csv import reader
import numpy as np
import requests

app = Flask(__name__)
app.config["DEBUG"] = True
# Upload folder
UPLOAD_FOLDER = 'static/files'

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
)

mycursor = mydb.cursor()
globalFilePath = ''

sql = "CREATE database IF NOT EXISTS CalypsoAI"
mycursor.execute(sql)

app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER
@app.route("/")
def index():
     tables = getTables()
     return render_template("index.html", all_tables = tables)

@app.route("/", methods=['POST'])
def uploadFiles():
     uploaded_file = request.files['file']
     if uploaded_file.filename != '':
          try:
               file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
               uploaded_file.save(file_path)
               parseCSV(file_path)
          except:
               flash("An Unexpected Error Occured, Please Try Again")
     else:
          flash("Please upload a valid file.")
     return redirect(url_for('index'))

def parseCSV(filePath):

     file_name = getName(filePath)
     col_names = getHeaders(filePath)
     my_csv = pd.read_csv(filePath,names=col_names, header=None)
     handleFormatting(my_csv, filePath)
     findEmptyState(my_csv, filePath)
     data_types = getDataTypes(col_names)
     createTable(file_name, col_names, data_types)
     a = open(filePath, 'r')
     my_reader = csv.DictReader(a)
     insert_sql = 'insert into ' + file_name + ' (' + ','.join(my_reader.fieldnames) + ') VALUES (' + ','.join(['%s'] * len(my_reader.fieldnames))+ ')'
     values = []
     for row1 in my_reader:
          row_values = []
          for field in my_reader.fieldnames:
               row_values.append(row1[field])
          values.append(row_values)
     for x in values:
          tupleList = tuple(x)
          insert_sql = 'insert into ' + file_name + ' (' + ','.join(my_reader.fieldnames) + ') VALUES (' + ','.join(['%s'] * len(my_reader.fieldnames))+ ')'
          val = tupleList
          try:
               mycursor.execute(insert_sql, val)
          except:
              flash('Insert failed, please try again')
     try:
          mydb.commit()
     except:
          flash('Error Committing file, please try again')

@app.route("/display/", methods=['POST'])
def displayCSV():
     tables = getTables()
     table_name = request.form.get("Display","")
     mycursor.execute('SELECT * FROM ' + table_name)
     table_rows = mycursor.fetchall()
     display_df = pd.DataFrame(table_rows, columns=mycursor.column_names)
     return render_template("index.html", all_tables = tables, display_table =[display_df.to_html(classes='data', header="true")])

@app.route("/stats/", methods=['POST'])
def statsOnCSV():
     tables = getTables()
     table_name = request.form['Stats']
     path = getPath(table_name)
     column_names = getHeaders(path)
     query = makeQuery(table_name)
     mycursor.execute(query)
     df_for_stats = DataFrame(mycursor.fetchall())
     df_for_stats.columns = column_names
     df_for_stats["age"] = pd.to_numeric(df_for_stats["age"])
     df_by_date  = df_for_stats.groupby('date') 
     stats_df = df_for_stats.groupby(['date']).agg([np.min, np.max, np.mean, np.median, np.size])
     stats_df.columns = [' Lowest Age ', ' Highest Age ', ' Mean ', ' Median ', ' Number of Unqiue Values ']
     return render_template("index.html", all_tables = tables, stats_table=[stats_df.to_html(classes='data', header="true")])
      
def makeQuery(table_name):
     query = "select * from " + table_name
     return query

def getPath(table_name):
     path = './'  + UPLOAD_FOLDER + '/' + table_name + '.csv'
     path = path.lower()
     return path

@app.route("/download/", methods=['POST'])
def downloadFile():
     files = os.listdir(UPLOAD_FOLDER)
     paths = [os.path.join(UPLOAD_FOLDER, basename) for basename in files]
     most_recent_path = max(paths, key=os.path.getctime)
     print('path:  ' + most_recent_path)
     return send_file(most_recent_path, as_attachment=True)

def handleFormatting(my_csv, filePath):
     try:
          for i,row in my_csv.iterrows():
               if(i is not 0):
                    row['date'] = datetime.datetime.strptime(row['date'], "%m/%d/%Y").strftime("%Y-%m-%d")
          my_csv.to_csv(filePath, index=False, header = None)
     except:
          flash('Please use the m/d/y date format ie: 1990-01-01')

     

def findEmptyState(my_csv, filePath):
     try:
          my_csv['state'] = my_csv['state'].replace(r'\s+', np.nan, regex=True)
          my_csv['state'] = my_csv['state'].fillna('BLANK')
          my_csv.to_csv(filePath, index=False, header = None)
     except:
          flash('State Column does not exist')


def getTables():
     mycursor.execute("USE CalypsoAI")
     mycursor.execute("SHOW TABLES")  
     tables = [v for (v, ) in mycursor]
     return tables

def getHeaders(filePath):
     with open(filePath, "rt", encoding= 'utf8') as f:
          d_reader = csv.DictReader(f)
          headers = d_reader.fieldnames
          return headers

def getName(filePath):
     csv_file = open(filePath)
     name = csv_file.name
     name = name.split("/")[-1].split('.')[0]
     return name

def getDataTypes(col_names):
     array_length = len(col_names)
     data_types = []
     for i in range(array_length):
          if('date' in col_names[i]):
               data_types.append('DATE')
          elif(len(col_names[i]) < 60):
               data_types.append('VARCHAR(60)')
          else:
               data_types.append('TEXT(255')
     return data_types 

def createTable(file_name, col_names, data_types):
     create_stement='create table if not exists '+file_name + '('
     i=0
     while i< len(col_names)-1 :
          create_stement =create_stement +col_names[i] +'  '+data_types[i]+' ,'
          i=i+1
     create_stement =create_stement +col_names[i] +'  '+data_types[i]+' )'
     mycursor.execute(create_stement)

def createPlaceholers(col_names):
     array_length = len(col_names)
     placeholders = []
     for i in range(array_length):
          placeholders.append('%s')
     return placeholders

def getRowValsAsList(filePath):
     row_lst = np.loadtxt(filePath, delimiter = ",", dtype="object")
     return row_lst

if (__name__ == "__main__"):
     app.run(port = 2000)