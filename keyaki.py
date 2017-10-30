import sys
from datetime import datetime
import requests
from bs4 import BeautifulSoup


class Keyaki:
    def __init__(self):
        self.ENTRYPOINT_ARTIST = "http://www.keyakizaka46.com/s/k46o/artist/"
        self.ENTRYPOINT_DIARY_MEMBER = "http://www.keyakizaka46.com/s/k46o/diary/member/"
        self.ENTRYPOINT_DIARY_DETAIL = "http://www.keyakizaka46.com/s/k46o/diary/detail/"

    def text_to_soup(self,text):
        return BeautifulSoup(text,"html.parser")

    def get(self,url,params=None):
        response = requests.get(url,params=params)
        response.raise_for_status()
        return response

    def get_diary_detail(self,id):
        try:
            id = str(int(id))
        except ValueError:
            print("Invalid id in getDiaryDetail")
            raise

        url = self.ENTRYPOINT_DIARY_DETAIL + id
        params = {
            "ima": "0000",
        }
        
        response = self.get(url,params=params)
        return response

    def parse_diary_detail(self,response):
        soup = self.text_to_soup(response.text)
        box_article = soup.find(attrs={"class": "box-article"})
        box_bottom = soup.find(attrs={"class": "box-bottom"})
        box_ttl = soup.find(attrs={"class": "box-ttl"})
        name = soup.find(attrs={"class": "name"})
        og_url = soup.find(attrs={"property": "og:url"})
        
        date = box_bottom.ul.li.string.strip()
        dt = datetime.strptime(date,"%Y/%m/%d %H:%M")
        images = box_article.find_all("img")
        image_urls = [ image["src"] for image in images ]
        title = box_ttl.h3.string.strip()
        name_string = name.a.string
        ct = name.a["href"].split("=")[-1]
        id = og_url["content"].split("=")[-1]
        return {
            "date": date,
            "datetime": dt,
            "images": image_urls,
            "title": title,
            "name": name_string,
            "ct": ct,
            "id": id,
        }

if __name__ == "__main__":
    keyaki = Keyaki()
    resp = keyaki.get_diary_detail(sys.argv[1])
    detail = keyaki.parse_diary_detail(resp)
    print(sorted(detail.items()))
    
