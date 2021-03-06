# mbMovieProc
===========

An all-in-one movie post-processor for creating MediaBrowser friendly movie libraries.

Read the mbMovieProc.INSTALL.txt for installation instructions before you do a get.

============

Version: 0.1
Author: Insodus

============
Install

To use this software, first you will need some dependencies.
    SOFTWARE: libxml, libxslt, mencoder
    PYTHON LIBS: requests, simplejson, tmdb, IMDbPY

I don't intend to write a tutorial on how to install this for all systems, this
information can be found freely on the internet. However if you are on a Debian
based system, you can acomplish this with two simple commands...

    sudo apt-get install libxml2-dev libxslt1-dev python-dev python-pip mencoder
    sudo pip install requests simplejson tmdb IMDbPY

This will most likely install a decent chunk of software (because mencoder has a
lot of dependencies).  However, it shouldn't be any more than 100mb or so.  If
you have software like VLC or mplayer, you'll likely already have these things
installed, so it won't add much to your system.

After these things are installed, you must get the latest mbMovieProc from github
and copy the scripts to your sabNzbd script folder. This can be accomplished by
doing the following (replace the sab folder with your own)...

    cd /tmp
    wget https://github.com/Insodus/mbMovieProc/archive/master.zip
    unzip master.zip
    cd mbMovieProc
    cp mbMovieProc.cfg mbMovieProc.py mbMovieReceiver.py ~/.sabnzbd/scripts/

Once this is complete, you must go to your scripts folder and update the config
file for your setup.  Edit mbMovieProc.cfg and look at the first few properties.

   MYMOVIEDIR: the path to your clean movie library
   MOVIE_NAME_FORMAT: the format you prefer your movies in
   WRITE_MB_MOVIE_XML: should it write a MediaBrowser xml? 1=true 0=false
   WRITE_BOXEE_MOVIE_NFO: should it write a Boxee nfo? 1=true 0=false
   MAX_BACKDROPS: Maximum number of backdrops to download
   KEEP_ORIG: should it leave the initial downloaded files? 1=true 0=false

Once that is complete, you must go into sabnzbd and set this as your primary
script for your movie category.  This is found under Config -> Categories.  For
your "movies" category, set it to the script "mbMovieReceiver.cfg".

I also highly recommend the nzbToMedia replacement scripts for sending notifications
to sickbeard and couchpotato.  In fact, if the scripts are in the same scripts folder
my script will attempt to use it for failure notifications.  Those scripts can be
found at this location (the install is almost identical to mine)...

    https://github.com/clinton-hall/nzbToMedia

Thats it, you should now be good to go.
