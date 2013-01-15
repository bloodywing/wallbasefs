import requests
import math
import base64
import re
import random
import os
import json

from HTMLParser import HTMLParser


baseurl = "http://wallbase.cc/"


class WallpaperParser(HTMLParser):
    def handle_data(self, data):
        pattern = re.compile("(?<=\'\+B\(\')[\w\+\/\=]+")
        if pattern.search(data):
            self.wallpaperurl = base64.b64decode(pattern.search(data).group(0))


class FavoriteParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == "span":
            for attr in attrs:
                print attr
                if "counter" in attr:
                    print attrs


class Wallbase(object):
    def __init__(self):
        self.headers = {"X-Requested-With": "XMLHttpRequest",
                        "Referer": baseurl + "user/favorites/-1/"}

    def do_login(self, user, passwd):
        payload = {"nopass": "0",
                   "pass": unicode(passwd),
                   "usrname": unicode(user)
                   }
        r = requests.post(baseurl + "user/login", data=payload)
        self.COOKIE = r.cookies
        return None


class Dynamics(Wallbase):
    """
    Needs Rework, this is really bugged now
    """
    def get_dynamics(self, searchstring, purify):
        payload = {"aspect": "0",
                   "board": "213",
                   "nsfw_nsfw": int(purify.get("nsfw")),
                   "nsfw_sfw": int(purify.get("sfw")),
                   "nsfw_sketchy": int(purify.get("sketchy")),
                   "orderby": "relevance",
                   "orderby_opt": "desc",
                   "query": searchstring,
                   "res": "0x0",
                   "res_opt": "eqeq",
                   "thpp": "40",
                   }

        wall_cats = {1: "manga-anime",
                     2: "rozne",
                     3: "high-resolution"
                     }
        dynamics = []
        search = []
        page = 0
        while search != [None]:
            resp = requests.post(url=baseurl + "search/" + page.__str__(),
                                 headers=self.headers, cookies=self.COOKIE, data=payload)
            search = json.loads(resp.content)
            for values in search:
                if search != [None]:
                    dynamics.append([unicode(values.get("id")), unicode(
                        wall_cats[values.get("attrs").get("wall_cat_id")])])
            page += 40
        return dynamics


class Favorites(Wallbase):
    def get_favorites_catalogues(self):
        resp = requests.get(
            url=baseurl + "user/favorites/-1/" + str(
                random.randint(1, 1000)),
            headers=self.headers, cookies=self.COOKIE)
        self.catalogues = []
        favorites = json.loads(resp.text)

        if favorites == []:
            return []

        self.catalogues.append([u"-1", u"Home"])

        for cat in favorites[0]:
            self.catalogues.append([cat[0].get("coll_id"), cat[0].get(
                "coll_title"), cat[0].get("fav_count")])

        return self.catalogues

    def add_collection(self, name):
        resp = requests.post(
            url=baseurl + "user/favorites_new/collection/" +
            str(random.randint(1, 1000)),
            headers=self.headers, cookies=self.COOKIE, data={"permissions": 1, "title": name})
        return None

    def get_wallpapers_for_catalogue(self, fav_id):
        total_wp = 0
        for cats in self.catalogues:
            if cats[0] == fav_id and cats[0] != u"-1":
                total_wp = float(cats[2])
        pages = math.ceil(total_wp / 40)

        offset = 0
        randint = str(random.randint(1, 1000))

        wallpaper = []
        wallpapers = None

        if fav_id == u"-1":
            while wallpapers != []:
                resp = requests.get(
                    url=baseurl + "user/favorites/-1/%d/0/" % offset + "666",
                    cookies=self.COOKIE,
                    headers=self.headers,
                )
                wallpapers = json.loads(resp.text)
                print wallpapers
                if wallpapers != []:
                    for values in wallpapers[0]:
                            wallpaper.append([unicode(values[0].get("wall_id")), unicode(values[0].get("wall_cat_dir"))])
                offset += 40
        else:
            wallpapers = None
            while wallpapers != []:
                resp = requests.post(
                    baseurl + "user/favorites/" +
                    fav_id.__str__() + "/%d/0/" % offset + "666",
                    cookies=self.COOKIE,
                    headers=self.headers,
                    data={"": ""}
                )
                wallpapers = json.loads(resp.text)
                if wallpapers != []:
                    for values in wallpapers[0]:
                        wallpaper.append([unicode(values[0].get("wall_id")), unicode(values[0].get("wall_cat_dir"))])
                offset += 40
        return wallpaper

    def _create_directories(self, basepath):
        for collection in self.catalogues:
            try:
                if not os.path.exists(os.path.join(basepath, collection[-2])):
                    os.makedirs(os.path.join(basepath, collection[-2]))
            except:
                print "Hmm.. something went wrong"


class Wallpaper(Wallbase):
    def get_wallpaper(self, id, cat_dir):
        self.parser = WallpaperParser()
        url = baseurl + "wallpaper/%s" % id
        resp = requests.get(url, cookies=self.COOKIE, prefetch=True)
        self.parser.feed(resp.content)
        if self.parser.wallpaperurl:
            result = dict({"url": self.parser.wallpaperurl,
                           "thumb": "http://wallbase1.org/sthumbs/" + cat_dir + "/thumb-" + id + ".jpg",
                           })
        else:
            result = None
        return result
