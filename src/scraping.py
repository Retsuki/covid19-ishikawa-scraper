import os
import csv
import glob
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup

from scraping_method import *

url = 'https://www.pref.ishikawa.lg.jp/kansen/coronakennai.html'
res = requests.get(url)
res.encoding = res.apparent_encoding
soup = BeautifulSoup(res.text, 'html.parser')

tmp_contents = soup.find(id='tmp_contents')
h1_contents = tmp_contents.find_all('h1')
all_contents_list = h1_contents[0].find_next_siblings()


# 陽性患者の属性を作成
df = pd.DataFrame([], columns=['date', '居住地', '年代', '性別'])
date, residence, age, sex = create_pacients_table_DataFrame(all_contents_list)

df['date'] = date
df['居住地'] = residence
df['年代'] = age
df['性別'] = sex

patients_df = df.sort_values('date').reset_index(drop=True)
patients_df.to_csv('./src/downloads/patients_data/patients.csv', index=False)
patients_df_dict = patients_df.to_dict('index')
data1 = [patients_df_dict.get(i) for i in range(len(patients_df_dict))]


# 陽性患者数データを作成
today = datetime.datetime.now()
this_year = today.year
this_month = today.month
this_day = today.day
this_hour = today.hour
this_minute = today.minute

date_column, subtotal_column = create_patients_column(
    this_year, this_month, this_day)
x_month_data = create_x_month_data(date, date_column, subtotal_column)
x_month_data.to_csv(
    './src/downloads/each_data/{}_{}.csv'.format(this_year, this_month), index=False)

csv_files = glob.glob('./src/downloads/each_data/*.csv')
each_csv = []
for i in csv_files:
    each_csv.append(pd.read_csv(i))
sum_x_month_data = pd.concat(each_csv).reset_index(drop=True)

patients_summary_df = sum_x_month_data.sort_values("日付").reset_index(drop=True)
patients_summary_df.to_csv("./src/downloads/final_data/total.csv", index=False)
patients_summary_df_dict = patients_summary_df.to_dict('index')
data2 = [patients_summary_df_dict.get(i)
         for i in range(len(patients_summary_df))]


# 市区町村別の感染者データを作成
table = soup.findAll("table")[0]
tr = table.findAll("tr")
with open('./src/downloads/table_data/corona_table.csv', "w", encoding="utf-8") as file:
    writer = csv.writer(file)
    for i in tr:
        row = []
        for cell in i.findAll(["td", "th"]):
            if cell.get_text() == '\u3000':
                row.append('市区町村')
            else:
                row.append(cell.get_text())
        writer.writerow(row)

table_df = pd.read_csv('./src/downloads/table_data/corona_table.csv')
table_df_no_tail = table_df.drop(20)
table_df_dict = table_df_no_tail.to_dict('index')
data3 = [table_df_dict.get(i) for i in range(len(table_df_no_tail))]


# 感染者数, 入院者数, 死亡者数, 退院数
final_row = table_df[-1:]
total_infect = int(final_row["感染者"])
treat = int(final_row["治療中"])
death = int(final_row["死亡"])
dischange = int(final_row["退院"])


# jsonデータを作成
update_at = "{}/{}/{} {}:{}".format(this_year,
                                    this_month, this_day, this_hour, this_minute)
data_json = {
    "lastUpdate": update_at,
    "patients": {
        "date": update_at,
        "data": data1
    },
    "patients_summary": {
        "date": update_at,
        "data": data2
    },
    "main_summary": {
        "attr": "検査実施人数",
        "value": 0,
        "children": [
            {
                "attr": "感染者者数",
                "value": total_infect,
                "children": [
                    {
                        "attr": "入院中",
                        "value": treat
                    },
                    {
                        "attr": "死亡",
                        "value": death
                    },
                    {
                        "attr": "退院",
                        "value": dischange
                    }
                ]
            }
        ]
    },
    "city_summary": {
        "lastUpdate": update_at,
        "data": data3
    }
}

with open('./src/data.json', 'w') as f:
    json.dump(data_json, f, indent=4, ensure_ascii=False)
