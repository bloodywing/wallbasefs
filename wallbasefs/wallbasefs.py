#!/usr/bin/env python
import fuse

import stat
import os
import time
import errno
import requests
import configobj
import wallbaseng as wallbase


cfg = configobj.ConfigObj(os.path.expanduser("~/.wallbasesync"))
user = ""
password = ""

_file_timestamp = int(time.time())

def getDepth(path):
    print "*** Depth", path 
    if path == '/':
        return 0
    else:
        return path.count('/')

def getParts(path):
    if path == '/':
        return [['/']]
    else:
        return path.split('/')

def loadfavorites(catalogues):
    l = dict()
    for directory in catalogues:
        l[directory[1]] =  {"size": directory[-1], "id": directory[0], "is_dir": True} # 0 is the favorites folder id
    return l

class RootInfo(fuse.Stat):
    def __init__(self, favorites):
        fuse.Stat.__init__(self)
        self.st_mode = stat.S_IFDIR | 0755
        self.st_nlink = 2
        self._favorites = {}
        self._favoritesobj = favorites

    @property
    def favorites(self):
        if not self._favorites:
            for f in self._favoritesobj._Favorites__get_favorites_catalogues():
                self._favorites[f[1]] = FavoriteInfo(self._favoritesobj, f)
        return self._favorites
        

class FavoriteInfo(fuse.Stat):
    def __init__(self, favoritesobj, f):
        fuse.Stat.__init__(self)
        self.st_atime = _file_timestamp  
        self.st_mtime = _file_timestamp  
        self.st_ctime = _file_timestamp
        self.st_mode = stat.S_IFDIR | 0755
        self.st_nlink = 2
        self._directory = favoritesobj
        self._folder = f
        self._images = {}
        wallpaper = wallbase.Wallpaper()
        wallpaper._Wallbase__do_login(user, password)
        self._wallpaper = wallpaper

    @property
    def images(self):
        if not self._images:
            for i in  self._directory._Favorites__get_wallpapers_for_catalogue(self._folder[0]):
                imageinfo = ImagesInfo(self._folder[0], self._wallpaper, i)
                print "*** Get Image", i[0]
                self._images["%s-%s.%s" % (self._folder[1], i[0], imageinfo.st_type)] = imageinfo
        return self._images
            

class ImagesInfo(fuse.Stat):
    def __init__(self, folderid, wallpaper, f):
        fuse.Stat.__init__(self)
        self._wallpaper = wallpaper
        self._link = self._wallpaper._Wallpaper__get_wallpaper(f[0], folderid)
        self.st_mode = stat.S_IFREG | 0644
        self.st_nlink = 1
        head = requests.head(self._link["url"])
        self.st_type = str(head.headers['content-type'].split("/")[1])
        self.st_size =  int(head.headers["content-length"])
        self.st_atime = _file_timestamp  
        self.st_mtime = _file_timestamp  
        self.st_ctime = _file_timestamp
        self._content = None

    @property
    def content(self):
        if self._content is None:
            print "**** Realimagesize", self.st_size
            r = requests.get(self._link["url"], prefetch=False)
            self._content = r.content
        return self._content

class WallbaseFS(fuse.Fuse):

    def __init__(self, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.big_writes = True
        #thread.start_new_thread(self.mythread, ())
        self.parser.add_option(mountopt="user", help="Your Wallbase.cc Username")
        self.parser.add_option(mountopt="password", help="Your Wallbase.cc Password")
        print "Init complete"
    
    def fsinit(self):
        
        print "Calling fsinit"
        
        
        global user
        global password
        
        self.user = self.cmdline[0].user
        self.password = self.cmdline[0].password
        if self.user:
            user = self.user
        else:
            user = cfg["user"]

        if self.password:
            password = self.password
        else:
            password = cfg["pass"]
        
        self.favorites = wallbase.Favorites()
        self.favorites._Wallbase__do_login(user, password)

        self.root = RootInfo(self.favorites)

    def split_path(self, path):
        if path == "/":
            return (None, None)

        parts = path.split('/')[1:]
        if len(parts) == 1:
            return (parts[0], None)
        else:
            return parts

    def getattr(self, path):
        print '*** getattr', path

        favfolder, image = self.split_path(path)

        if favfolder is None:
            stat = self.root
        else:
            print "*** Not Root", favfolder
            stat = self.root.favorites.get(favfolder)
            if not stat:
                return -errno.ENOENT
            if image:
                stat = stat.images.get(image)
                if not stat:
                    return -errno.ENOENT
        return stat


    def getdir(self, path):
        print '*** getdir', path
        return -errno.ENOSYS

    def mythread ( self ):
        print '*** mythread'
        return -errno.ENOSYS

    def chmod ( self, path, mode ):
        print '*** chmod', path, oct(mode)
        return -errno.ENOSYS

    def chown ( self, path, uid, gid ):
        print '*** chown', path, uid, gid
        return -errno.ENOSYS

    def fsync ( self, path, isFsyncFile ):
        print '*** fsync', path, isFsyncFile
        return -errno.ENOSYS

    def link ( self, targetPath, linkPath ):
        print '*** link', targetPath, linkPath
        return -errno.ENOSYS

    def mkdir ( self, path, mode ):
        print '*** mkdir', path, oct(mode)
        return -errno.ENOSYS

    def mknod ( self, path, mode, dev ):
        print '*** mknod', path, oct(mode), dev
        return -errno.ENOSYS

    def open ( self, path, flags ):
        print '*** open', path, flags
        access_flags = os.O_RDONLY | os.O_RDWR
        if flags & access_flags != os.O_RDONLY:
            print "Error", access_flags
            return -errno.EACCES
        else:
            return 0
            
    def read(self, path, size, offset, fh=None):
        print '*** read', path, size, offset, fh
        favfolder, image = self.split_path(path)
        print "Image:", image
        print "Favorites:", favfolder
        imageinfo = self.root.favorites[favfolder].images[image]
        print "Offset", offset
        print "Size", imageinfo.st_size
        if imageinfo.st_size:
            print "Here is your image"
            content = imageinfo.content[offset:offset+size]
            return content
        else:
            return ''

    def readdir(self, path, offset):
        yield fuse.Direntry(".")
        yield fuse.Direntry("..")
        if path == "/":
            entries = self.root.favorites.keys()
        else:
            entries = self.root.favorites[path[1:]].images.keys();
        
        for e in entries:
            yield fuse.Direntry(str(e))

    def readlink ( self, path ):
        print '*** readlink', path
        return -errno.ENOSYS

    def release ( self, path, flags ):
        print '*** release', path, flags
        return -errno.ENOSYS

    def rename ( self, oldPath, newPath ):
        print '*** rename', oldPath, newPath
        return -errno.ENOSYS

    def rmdir ( self, path ):
        print '*** rmdir', path
        return -errno.ENOSYS

    def statfs ( self ):
        print '*** statfs'
        stats = fuse.StatVfs()
        return stats

    def symlink ( self, targetPath, linkPath ):
        print '*** symlink', targetPath, linkPath
        return -errno.ENOSYS

    def truncate ( self, path, size ):
        print '*** truncate', path, size
        return -errno.ENOSYS

    def unlink ( self, path ):
        print '*** unlink', path
        return -errno.ENOSYS

    def utime ( self, path, times ):
        print '*** utime', path, times
        return -errno.ENOSYS

    def write ( self, path, buf, offset ):
        print '*** write', path, buf, offset
        return -errno.ENOSYS


def main():
    fuse.fuse_python_api = (0, 2)
    fuse.feature_assert('stateful_files', 'has_init')
    
    fs = WallbaseFS()
    fs.parse(errex=1)
    fs.multithreaded = True
    fs.main()

if __name__ == "__main__": main()
