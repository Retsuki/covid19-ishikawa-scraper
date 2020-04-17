import re
import jaconv
import datetime
import collections
import pandas as pd


# 日本語日付を「xx-xx-xx」の形に変更する関数
def data_shaping(date):
    m = re.match(r'[0-9]+月[0-9]+日', date)
    m_text = m.group()
    pos = re.split('[月日]', m_text)
    datetime_data = datetime.datetime(2020, int(pos[0]), int(pos[1]))
    date = datetime_data.strftime("%Y-%m-%d")
    return date

# 感染確認日を文字列から抽出する関数
def extraction_date(new_text_list):
    date = []
    for i in new_text_list:
        target_index = i.find("陽性と判明")
        result = i[:target_index]
        s = re.findall(r'[0-9]+月[0-9]+日', result)
        new_data = data_shaping(s[-1])
        date.append(new_data)
    return date

# 年代, 性別, 居住地, 感染確認日のそれぞれのリストを作成する関数
def create_pacients_table_DataFrame(all_contents_list):
    residence = []
    age = []
    sex = []
    now_age = ""
    new_text = ""
    new_text_list = []
    infect_count = 0
    for i in all_contents_list:
        text = i.get_text()
        text2 = jaconv.z2h(text, kana=False, digit=True, ascii=True).replace(" ", "").replace(":", "").replace("\xa0", "")

        if "(1)年代" in text2:
            m = re.search(r"\(1\)?年代(.+)", text2)
            text_age = m.groups()[0]
            age.append(text_age)

        elif "(2)性別" in text2:
            m = re.search(r"\(2\)性別(.+)", text2)
            text_sex = (m.groups()[0])
            sex.append(text_sex)

        elif "(3)居住地" in text2:
            m = re.search(r"\(3\)居住地(.+)", text2)
            text_residence = (m.groups()[0])
            residence.append(text_residence)

        if "症状・経過" in text2:

            # 新たなlistの要素を作る
            new_text_list.append("empty")

            # text2が「症状・経過」文字列だった場合に
            # 「check」をつけて、次の「症状・経過」まで文字列を結合させる
            # それにより後ほど日付データを抽出できるようになる
            if now_age == "":
                now_age = text2 + "check"
                new_text += text2
                infect_count += 1
                continue

            # now_ageとtext2の内容が違うのであれば
            # (1)Save ever data
            # (2)Delete now data
            # (3)Add new data to now data
            if now_age != text2:
                new_text_list[infect_count-1] = new_text # (1)
                new_text = "" # (2)
                new_text += text2 # (3)
                infect_count += 1
                continue

        # 行動歴のデータは不要なので、「行動歴」項目があればスキップ
        if 0 < infect_count:
            if "(5)行動歴" in text2:
                continue
            new_text += text2

    new_text_list[infect_count-1] = new_text
    date = extraction_date(new_text_list)
    return date, residence, age, sex

# 日付と日別感染者数、２つデータの作成する関数
def create_patients_column(this_year, this_month, this_day):
    today_info = datetime.datetime(this_year, this_month, 1)
    start_date = today_info.strftime("%Y-%m-%d")
    date_column = pd.date_range(start_date, freq='D', periods=this_day)
    subtotal_column = [0 for i in range(this_day)]
    return date_column, subtotal_column

# pacients_summary_DataFrameを作成する関数
def create_x_month_data(date, date_column, subtotal_column):
    # 空のデータフレームの作成
    progress_map = {'日付': date_column, '小計': subtotal_column}
    df = pd.DataFrame(progress_map)

    # 条件にマッチした日にデータを挿入
    infect_date_count = collections.Counter(date)
    for num, i in enumerate(df.iloc[0:, 0]):
        for j in infect_date_count.keys():
            if j in str(i):
                df.iloc[num, 1] = infect_date_count[j]
    return df