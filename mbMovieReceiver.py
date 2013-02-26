#!/usr/bin/env python

import sys
import os
import mbMovieProc

print "Starting mbMovieProc v0.1 - by Insodus"

if len(sys.argv) != 8:
    print "Script not triggered from sabnzbd, aborting..."
    sys.exit(1)

jobName = sys.argv[1]
status = int(sys.argv[7])

print "Job: ", jobName
print "Status: ", str(status)

if status > 0:
    #link to clinton-hall's couchpotato notifier if its here...
    hallsCfgFile = os.path.join(os.path.dirname(sys.argv[0]), 'autoProcessMedia.cfg')
    if os.path.isfile(hallsCfgFile):
        print "Sending to clinton-hall\'s nzbToMedia..."
        import autoProcessMovie
        autoProcessMovie.process(sys.argv[1], sys.argv[2], sys.argv[7])
        sys.exit(1)
    else:
        print "It seems the download failed, aborting..."
        sys.exit(1)

configFile = os.path.join(os.path.dirname(sys.argv[0]), 'mbMovieProc.cfg')

print "Starting process..."
myProc = mbMovieProc.mbMovieProc(configFile)
myProc.process(jobName)
print "Done!"
