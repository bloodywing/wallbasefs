#!/usr/bin/env python

import os
import stat
from configobj import ConfigObj
from time import time
from multiprocessing import Pipe, Process
from sys import argv, exit
from wallbase import Wallbase
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn


cfg = ConfigObj(os.path.expanduser("~/.wallbasesync"))


class Wallbasefs(LoggingMixIn, Operations):
    """
    
    In order to use this class properly you need to have
    a wallbase.cc account. Loading your favorites can be really
    slow depending on your internet speed and the size of your
    favorites.

    """    
    def __init__(self, username, password):

        if not username:
            username = cfg["user"]

        if not password:
            password = cfg["password"]

        self.wb = Wallbase(username, password)
        self.wb.get_collections()
        self.files = {}
        self.p_conn, c_conn = Pipe()
        p = Process(target=self.wallpaper_worker, args=(c_conn,))
        p.start()

    def __call__(self, op, path, *args):
        return super(Wallbasefs, self).__call__(op, path, *args)

    def wallpaper_worker(self, conn):
        """
        Tries to preload collections in background
        """
        files = {}
        print "working ...."
        for c in self.wb.collections:
            for w in self.wb.get_wallpapers_by_cid(c.cid):
                name = unicode("_").join(w.tags)[:200] + "_%s.%s" % (unicode(w.wid), w.extension)
                if not files.has_key("/%s/%s" % (c.name , name)):
                    files["/%s/%s" % (c.name , name)] = dict()
                attrs = files["/%s/%s" % (c.name , name)].setdefault('attr', {})
                attrs["blob"] = w.blob
                attrs["size"] = len(attrs["blob"])
            conn.send(files)
        conn.close()
                

    def getattr(self, path, fh=None):
        print "*** getattr", path, fh
        if path == "/":
            st = os.lstat(path)
            return dict(
                (key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                    'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        elif path.endswith("png") or path.endswith("jpg"):
            st_size = self.getxattr(path, "size")
            return dict(st_mode=stat.S_IFREG | 0644, st_nlink=1, st_size=st_size)
        else:
            return dict(st_mode=stat.S_IFDIR | 0644, st_nlink=1, st_size=0)

    def getxattr(self, path, name, position=0):
        print "*** getxattr", path, name, position
        attrs = self.files[path].get("attr", {})
        try:
            return attrs[name]
        except KeyError:
            return "" 

    def listxattr(self, path):
        print "*** listxattr", path
        attrs = self.files[path].get("attr", {})
        return attrs.keys()

    def setxattr(self, path, name, value, options, position=0):
        print "*** setxattr", path, name, value, options, position

    def read(self, path, size, offset, fh=None):
        print '*** read', path, size, offset, fh
        blob = self.getxattr(path, "blob")
        return blob[offset:offset + size]

    def readdir(self, path, fh):
        print "*** readdir", path, fh
        while self.p_conn.poll():
            self.files.update(self.p_conn.recv())
        entries = [".", ".."]
        if path == "/":
            return entries + [
                c.name.encode("utf-8") for c in self.wb.collections
            ]
        else:
            for c in self.wb.collections:
                if c.name == path[1:]:
                    wallpapers = self.wb.get_wallpapers_by_cid(c.cid)
                    for w in wallpapers:
                        name = unicode("_").join(w.tags)[:200] + "_%s.%s" % (unicode(w.wid), w.extension)
                        entries.append(name)
                        if not self.files.has_key("%s/%s" % (path , name)):
                            self.files["%s/%s" % (path , name)] = dict()
                        attrs = self.files["%s/%s" % (path , name)].setdefault('attr', {})
                        attrs["wid"] = w.wid
                        attrs["tags"] = w.tags

                        if not attrs.has_key("blob"):
                            attrs["blob"] = w.blob
                            attrs["size"] = len(attrs["blob"])
                    return entries

if __name__ == "__main__":
    if len(argv) != 4:
        print("Usage: %s <username> <password> <mountpoint>" % argv[0])
        exit(1)

    fuse = FUSE(Wallbasefs(argv[1], argv[2]), argv[3])
