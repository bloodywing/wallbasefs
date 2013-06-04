"""Wallbase.cc library used by wallbasefs

.. moduleauthor:: Pierre Geier <pierre@neocomy.net>

"""
import re
import base64
import requests
from math import ceil
from random import randint
from HTMLParser import HTMLParser

#  Static stuff like Wallbase.cc URL

URL = "http://wallbase.cc/"
session = requests.Session()
jsonheaders = {"X-Requested-With": "XMLHttpRequest"}


class Wallbase(object):

    def __init__(self, username, password):
        """
        Args:
           username (str): a Wallbase.cc Login
           password (str): The Users Password
        """
        self.collections = CollectionsList()
        self._login(username, password)
                    #  First thing we need to do: log the user in

    def _login(self, username, password):
        response = session.post("%suser/login" % URL,
                data={"usrname": username,"pass":password},
                allow_redirects=False)
        return response.cookies

    def get_collections(self):
        response = session.get(
            "%suser/favorites/-1/%d" % (URL, randint(1, 1000)),
                headers=jsonheaders)
        if response.status_code == 200:
            json = response.json()

            self.collections.append(Collection())  # Adds 'Home'

            for c in json[0]:
                collection_dict = c.pop()
                self.collections.append(
                    Collection(cid=int(collection_dict["coll_id"]),
                        public=collection_dict["coll_permissions"],
                        name=collection_dict["coll_title"],
                        fav_count=int(collection_dict["fav_count"])))
        return self.collections

    def add_collection(self, collname, permission=0):
        response = session.post(
            "%suser/favorites_new/collection/%d" % (URL, randint(1,1000)), data={"title": collname, "permissions": permission}, headers=jsonheaders, allow_redirects=False)
        if response.status_code == 200:
            return True
        else:
            return False


    def get_wallpapers_by_cid(self, cid):

        if not len(self.collections):
            raise RuntimeWarning("Please call get_collections() first")

        wallpapers = []
        page_offset = 0
        collection = self.collections.get_by_cid(cid)
        pages = ceil(collection.fav_count / 40.0)

        if not collection.wallpapers:
            while True:
                response = session.get("%suser/favorites/%d/%d/0/666" % (
                    URL, cid, page_offset), headers=jsonheaders)

                if not len(response.json()):
                    return collection.wallpapers
                else:
                    json = response.json().pop()
                    for wallpaper in json:
                        w = wallpaper.pop()
                        tags = w["wall_tags"].split("|")[0::4]
                        collection.wallpapers.append(
                                Wallpaper(wid=int(w[
                                          "wall_id"]), cid=cid, wall_cat_dir=w["wall_cat_dir"], wall_imgtype=int(w["wall_imgtype"]), tags=tags)
                        )
                        page_offset += 40
        return collection.wallpapers


class CollectionsList(list):

    """
    makes it easy to handle the collections
    """
    def get_by_cid(self, cid):
        for c in self:
            if c.cid == cid:
                return c


class Collection(object):

    def __init__(self, public=False, cid=-1, name="Home", fav_count=0):
        self.cid = cid
        self.name = name
        self.public = public
        self.fav_count = fav_count
        self.wallpapers = []

    def __repr__(self):
        return "<%d, %s>" % (self.cid, self.name)


class Wallpaper(object):

    def __init__(self, wid, cid, wall_cat_dir, wall_imgtype=1, tags=[]):
        self.wid = wid
        self.cid = cid
        self.wall_cat_dir = wall_cat_dir
        self.wall_imgtype = wall_imgtype
        self.tags = tags

    @property
    def extension(self):
        if self.wall_imgtype == 2:
            return "png"
        else:
            return "jpg"


    @property
    def blob(self):
        return session.get(self.url).content

    @property
    def url(self):
        parser = WallpaperParser()
        response = session.get("%swallpaper/%d" % (URL, self.wid))
        parser.feed(response.content)
        if parser.wallpaperurl:
            return parser.wallpaperurl


class WallpaperParser(HTMLParser):

    def handle_data(self, data):
        pattern = re.compile("(?<=\'\+B\(\')[\w\+\/\=]+")
        if pattern.search(data):
            self.wallpaperurl = base64.b64decode(pattern.search(data).group(0))
