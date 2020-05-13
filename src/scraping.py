import io
import re
import os
import csv
import glob
import json
import requests
import datetime
import collections
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup


# スクレイピング用のhtmlデータ
html_url = 'https://www.pref.ishikawa.lg.jp/kansen/coronakennai.html'
html_res = requests.get(html_url)
html_res.encoding = html_res.apparent_encoding
soup = BeautifulSoup(html_res.text, 'html.parser')

# オープンデータ（陽性感染者属性）
csv_url = 'https://www.pref.ishikawa.lg.jp/kansen/documents/170003_ishikawa_covid19_patients.csv'
save_path = './new_src/pacients.csv'
csv_res = requests.get(csv_url).content
df = pd.read_csv(io.StringIO(csv_res.decode('shift-jis')))


# 患者の属性データを作成 --------------------------------------->
# 必要のないカラムは削除
patients_df = df.drop(['No', '都道府県名', '全国地方公共団体コード', '市区町村名'], axis=1)
patients_df = patients_df.rename(
    columns={'公表_年月日': 'date', '患者_居住地': '居住地', '患者_年代': '年代', '患者_性別': '性別'})

# apply関数でstr_to_dateを「公表_年月日」カラムに適用
# 「2020-05-13 00:00:00」 -> 「2020-05-13」
# 文字列から日付に変換


def str_to_date(x):
    date_dt = str(datetime.datetime.strptime(x, '%Y/%m/%d'))
    return str(date_dt).split(' ')[0]


patients_df['date'] = patients_df['date'].apply(str_to_date)
patients_df.to_csv('./src/downloads/patients_data/patients.csv', index=False)
patients_df_dict = patients_df.to_dict('index')
data1 = [patients_df_dict.get(i) for i in range(len(patients_df_dict))]


# 日別、陽性患者数データを作成 --------------------------------------->
date = patients_df['date'].values.tolist()
today = datetime.datetime.now()
this_year = today.year
this_month = today.month
this_day = today.day
this_hour = today.hour
this_minute = today.minute

# 2月から当月までのdate_rangeを作成
start_day = datetime.datetime(this_year, 2, 1)
start_date = start_day.strftime("%Y-%m-%d")
now_day = datetime.datetime(this_year, this_month, this_day)
now_date = now_day.strftime("%Y-%m-%d")
date_range = pd.date_range(start_date, now_date, freq='D')
date_column = [str(i).split(' ')[0] for i in date_range]
subtotal_column = [0 for i in range(len(date_column))]

# 空の日別データを作成
progress_map = {'日付': date_column, '小計': subtotal_column}
each_day_df = pd.DataFrame(progress_map)
each_day_df.tail()

# 空の日別データにデータを挿入
infect_date_count = collections.Counter(date)
for num, i in enumerate(each_day_df.iloc[0:, 0]):
    if i in infect_date_count.keys():
        each_day_df.iloc[num, 1] = infect_date_count[i]

each_day_df.to_csv("./src/downloads/final_data/total.csv", index=False)
each_day_df_dict = each_day_df.to_dict('index')
data2 = [each_day_df_dict.get(i) for i in range(len(each_day_df))]


# 市区町村別の「感染者, 退院, 死亡, 治療中」データを作成 --------------------------------------->
# tableデータをcsvに変換
table = soup.findAll("table")[0]
tr = table.findAll("tr")
with open('./src/downloads/table_data/corona_table.csv', "w", encoding="utf-8") as file:
    writer = csv.writer(file)
    for i in tr:
        row = []
        for cell in i.findAll(["td", "th"]):
            if cell.get_text() == '\u3000':
                row.append('居住地')
            else:
                row.append(cell.get_text())
        writer.writerow(row)

table_df = pd.read_csv('./src/downloads/table_data/corona_table.csv')
table_df = table_df.rename(columns={table_df.columns[-1]: '備考'})
minus_one_table_df = table_df.drop(20)
table_df_dict = minus_one_table_df.to_dict('index')
data3 = [table_df_dict.get(i) for i in range(len(minus_one_table_df))]


# 居住地別の感染者数データの作成 --------------------------------------->
residence_patients_df = minus_one_table_df.drop(
    columns=['退院', '死亡', '治療中', '備考'])
residence_patients_df.to_csv(
    "./src/downloads/residence_pacients/total.csv", index=False)
residence_patients_df_dict = residence_patients_df.to_dict('index')
data4 = [residence_patients_df_dict.get(i)
         for i in range(len(residence_patients_df))]
data4

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
    },
    "residence_pacients": {
        "lastUpdate": update_at,
        "data": data4
    }
}

with open('./src/data.json', 'w') as f:
    json.dump(data_json, f, indent=4, ensure_ascii=False)
