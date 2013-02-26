#!/usr/bin/env python

import mbMovieProc
import unittest
import os
import sys
import shutil

class mbMovieProcTests(unittest.TestCase):
    theTestFolder = "/tmp/mbTests/"

    def setUp(self):
        self.printLabel("Starting setup")
        if os.path.exists(self.theTestFolder):
            print "Test folder already exists, removing it"
            shutil.rmtree(self.theTestFolder)

        print "Creating test folder"
        os.mkdir(self.theTestFolder)
        os.mkdir(os.path.join(self.theTestFolder, "Finished"))

    def tearDown(self):
        self.printLabel("Tearing down")
        print "Listing final structure, and removing "
        self.listTestfolder()
        shutil.rmtree(self.theTestFolder)

    def listTestfolder(self):
        for path,dirs,files in os.walk(self.theTestFolder):
            for subdir in dirs:
                print os.path.join(path, subdir) + "/"
            for fn in files:
                print os.path.join(path,fn)

    def printLabel(self, label):
        print "******************************"
        print "**** ", label

    def doTestProcessByConfig(self, configName, movieName):
        print "Opening config file and starting tests..."
        configFile = os.path.join(os.getcwd(), configName)
        print "Config:", configFile
        myMBProc = mbMovieProc.mbMovieProc(configFile)

        print "Adding basic movie structure"
        testFullFolder = os.path.join(self.theTestFolder, movieName)
        os.mkdir(testFullFolder)
        open(os.path.join(testFullFolder, movieName + ".nfo"), 'w').close()
        open(os.path.join(testFullFolder, movieName + ".srt"), 'w').close()
        open(os.path.join(testFullFolder, movieName + ".avi"), 'w').close()
        open(os.path.join(testFullFolder, movieName + ".sample.avi"), 'w').close()
        print "Done.  Listing test structure..."
        self.listTestfolder()

        print "Executing process..."
        myMBProc.process(testFullFolder)

    def testBasicMovie(self):
        self.printLabel("Starting testBasicMovie")
        test1MovieName = "the.hobbit.an.unexpected.journey.2012.XViD.720p.Movies"
        self.doTestProcessByConfig("mbMovieTests1.cfg", test1MovieName)

    def testNoKeepMovie(self):
        self.printLabel("Starting testBasicMovie")
        test2MovieName = "Lincoln.2012.XViD.720p.Movies"
        self.doTestProcessByConfig("mbMovieTests2.cfg", test2MovieName)


#add execution capability
def main():
    unittest.main()

if __name__ == '__main__':
    main()
