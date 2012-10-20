wallbasefs
==========

FuseFS Module for wallbase.cc


Usage
-----
    ./wallbasefs.py /mountpoint -ouser=userxx,password=changeme

Try ./wallbasefs.py -h to see other fusefs options


Bugs
----
Huge Favoritecollection take long to load

Config File
-----------
Create a file called `.wallbasesync` in your $HOME

    user=yourusername
    pass=changeme

yourusername = Your login on wallbase.cc
changeme = Your password on wallbase.cc

Set the file to read/write only for the current user.
    chmod o-rw ~/.wallbasesync

Missing Features
----------------
No add, remove etc. for your Favorites, maybe added in future releases.
Currently this FS is read only
