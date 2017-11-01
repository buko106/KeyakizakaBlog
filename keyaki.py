import sys
from datetime import datetime
import requests
from bs4 import BeautifulSoup


class Keyaki:
    """
    Method whose name begins with "get" actually creates HTTP request,
    and returns a response. Method whose name begins with "parse" converts
    response to a dict including infomation obtaind from a response.
    """
    def __init__(self):
        self.ENTRYPOINT_DOMAIN = "http://www.keyakizaka46.com"
        self.ENTRYPOINT_PREFIX = self.ENTRYPOINT_DOMAIN + "/s/k46o"
        self.ENTRYPOINT_ARTIST = self.ENTRYPOINT_PREFIX + "/artist"
        self.ENTRYPOINT_DIARY_MEMBER = self.ENTRYPOINT_PREFIX + "/diary/member"
        self.ENTRYPOINT_DIARY_DETAIL = self.ENTRYPOINT_PREFIX + "/diary/detail"
        self.MAXIMUM_CT = 42

    # utils
    @staticmethod
    def text_to_soup(text):
        return BeautifulSoup(text, "html.parser")

    @staticmethod
    def convert_ct(ct):
        try:
            ct = "%02d" % int(ct)
            return ct
        except ValueError:
            print("Invalid value of ct")
            raise

    @staticmethod
    def dump_as_json(data, path=None):
        import json
        kwargs = {"indent": 2, "ensure_ascii": False, "sort_keys": True}
        if path:
            return json.dump(data, open(path, "wt"), **kwargs)
        else:
            return json.dumps(data, **kwargs)

    def _convert_href_to_url_and_extract_id(self, input_dict):
        import copy
        result_dict = copy.deepcopy(input_dict)

        result_dict["id"] = result_dict["href"].split("?")[0].split("/")[-1]
        result_dict["url"] = self.ENTRYPOINT_DOMAIN + result_dict["href"]
        return result_dict

    def get(self, url, params=None):
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response

    # getter
    def get_diary_detail(self, id):
        try:
            id = str(int(id))
        except ValueError:
            print("Invalid id in get_diary_detail")
            raise

        url = self.ENTRYPOINT_DIARY_DETAIL + "/" + id
        params = {
            "ima": "0000",
        }

        response = self.get(url, params=params)
        return response

    def get_artist(self, ct):
        ct = self.convert_ct(ct)
        url = self.ENTRYPOINT_ARTIST + "/" + ct
        params = {
            "ima": "0000",
        }

        response = self.get(url, params=params)
        return response

    def _get_global_latest_diary(self):
        url = self.ENTRYPOINT_DIARY_MEMBER
        return self.get(url)

    def _get_latest_diary_by_ct(self, ct):
        ct = self.convert_ct(ct)
        url = self.ENTRYPOINT_DIARY_MEMBER + "/" + "list"
        params = {
            "ima": "0000",
            "ct": ct,
        }
        return self.get(url, params=params)

    # parser
    def parse_diary_detail(self, response):
        soup = self.text_to_soup(response.text)
        box_article = soup.find(attrs={"class": "box-article"})
        box_bottom = soup.find(attrs={"class": "box-bottom"})
        box_ttl = soup.find(attrs={"class": "box-ttl"})
        name = soup.find(attrs={"class": "name"})
        og_url = soup.find(attrs={"property": "og:url"})

        date = box_bottom.ul.li.string.strip()
        dt = datetime.strptime(date, "%Y/%m/%d %H:%M")
        images = box_article.find_all("img")
        image_urls = [image["src"] for image in images]
        title = box_ttl.h3.string.strip()
        name_string = name.a.string
        ct = name.a["href"].split("=")[-1]
        id = og_url["content"].split("=")[-1]
        return {
            "response": response,
            "date": date,
            "datetime": dt,
            "images": image_urls,
            "title": title,
            "name": name_string,
            "ct": ct,
            "id": id,
        }

    def parse_artist(self, response):
        soup = self.text_to_soup(response.text)
        box_profile_img = soup.find(attrs={"class": "box-profile_img"})
        box_profile_text = soup.find(attrs={"class": "box-profile_text"})
        box_info = soup.find(attrs={"class": "box-info"})
        dls = box_info.find_all("dl")

        profile_img_url = box_profile_img.img["src"]
        furigana = box_profile_text.find(
            attrs={"class": "furigana"}
        ).string.strip()
        # NOTE: replace white space(\u3000) with ascii white space
        en = box_profile_text.find(
            attrs={"class": "en"}
        ).string.strip().replace("\u3000", " ")
        jp_to_en = {
            "生年月日": "birthday",
            "血液型": "blood_type",
            "身長": "height",
            "出身地": "birthplace",
            "星座": "constellation",
        }

        dl_dict = {}
        for dl in dls:
            dd = dl.find("dd").string.strip().rstrip(":")
            key = jp_to_en.get(dd, dd)  # convert to english if possible.
            dt = dl.find("dt").string.strip()
            dl_dict[key] = dt

        return {
            **dl_dict,
            "response": response,
            "profile_img_url": profile_img_url,
            "furigana": furigana,
            "en": en,
        }

    def _parse_diary_member_list(self, response):
        soup = self.text_to_soup(response.text)
        box_ttl = soup.find(attrs={"class": "box-ttl"})
        href = box_ttl.h3.a["href"]
        title = box_ttl.h3.a.string.strip()
        return {
            "response": response,
            "href": href,
            "title": title,
        }

    def _parse_global_latest_diary(self, response):
        soup = self.text_to_soup(response.text)
        slider = soup.find("div", attrs={"class": "slider"})
        href = slider.ul.li.a["href"]
        title = slider.ul.li.p.string.strip()
        return {
            "response": response,
            "href": href,
            "title": title,
        }

    # API
    def diary_detail(self, id):
        return self.parse_diary_detail(
            self.get_diary_detail(id)
        )

    def latest_diary(self, ct=None):
        if ct is None:
            result = self._parse_global_latest_diary(
                self._get_global_latest_diary()
            )
            return self._convert_href_to_url_and_extract_id(result)
        else:
            result = self._parse_diary_member_list(
                self._get_latest_diary_by_ct(ct)
            )
            return self._convert_href_to_url_and_extract_id(result)

    def artist(self, ct=None):
        if ct is None:
            result = {}
            for i in range(1, self.MAXIMUM_CT+1):
                ct = self.convert_ct(i)
                try:
                    result[ct] = self.parse_artist(self.get_artist(ct))
                except Exception as e:
                    print(e)
            return result
        else:
            ct = self.convert_ct(ct)
            return self.parse_artist(self.get_artist(ct))

if __name__ == "__main__":
    keyaki = Keyaki()
    resp = keyaki.get_diary_detail(sys.argv[1])
    detail = keyaki.parse_diary_detail(resp)
    print(sorted(detail.items()))

    keyaki.dump_as_json(keyaki.artist(), "members.json")
