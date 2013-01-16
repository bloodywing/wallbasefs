#!/usr/bin/env python

from pyftpdlib.ftpserver import FTPHandler
from pyftpdlib.ftpserver import FTPServer
from pyftpdlib.ftpserver import DummyAuthorizer

import configobj
import os

###
# This is a ftp server component of wallbasefs, because
# fuse is not windows compatible yet.
###

class WallbaseFSHandler(FTPHandler):

    def on_connect(self):
        print "%s:%s connected" % (self.remote_ip, self.remote_port)

    def on_disconnect(self):
        # do something when client disconnects
        pass

	def on_login(self, username):
		print username
		pass

	def on_logout(self, username):
		pass

def main():
	cfg = configobj.ConfigObj(os.path.expanduser("~/.wallbasesync"))
	user = cfg["user"]
	password = cfg["pass"]
	
	authorizer = DummyAuthorizer()
	authorizer.add_user(user, password, homedir='.', perm='elr')

	handler = WallbaseFSHandler
	handler.authorizer = authorizer
	server = FTPServer(('', 2221), handler)
	server.serve_forever()

if __name__ == "__main__":
	main()