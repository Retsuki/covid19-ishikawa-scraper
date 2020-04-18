import json
import urllib
import feedparser

keyword = "石川県コロナ"
query = urllib.parse.quote(keyword)
url = 'https://news.google.com/rss/search?q=' + query + '&hl=ja&gl=JP&ceid=JP:ja'
d = feedparser.parse(url)

news = []
for num, entry in enumerate(d.entries):
    if num > 5:
        break
    pub_day = entry.published_parsed
    published_parsed = "%04d/%02d/%02d %02d:%02d" % (
        pub_day.tm_year, pub_day.tm_mon, pub_day.tm_mday, pub_day.tm_hour, pub_day.tm_min)
    tmp = {
        "date": published_parsed,
        "url": entry.link,
        "text": entry.title
    }
    news.append(tmp)

news = sorted(news, key=lambda x: x['date'], reverse=True)

json_data = {
    "newsItems": news
}

with open('./src/news.json', 'w') as f:
    json.dump(json_data, f, indent=4, ensure_ascii=False)
