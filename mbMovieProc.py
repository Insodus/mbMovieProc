#!/usr/bin/env python

#name: mbMovieProc
#desc: An all-in-one movie post-processor for creating MediaBrowser friendly movie libraries.
#author: Insodus
#version: 0.1

import ConfigParser
import sys
import os
import re
import tmdb
import imdb
import urllib2
import difflib
import shutil
import unicodedata

class mbMovieProc:
    #configs, with defaults
    MYMOVIEDIR = ""
    TMDB_API = ""
    MOVIE_NAME_FORMAT = ""
    WRITE_MB_MOVIE_XML = 0
    WRITE_BOXEE_MOVIE_NFO = 0
    MAX_BACKDROP = 0
    KEEP_ORIG = 1
    MIN_RATIO = 1.0
    
    def __init__(self, configFile):
        print "Config:", configFile
        if not os.path.isfile(configFile):
            raise Exception("Could not find configFile specified: " + configFile)

        config = ConfigParser.ConfigParser()
        config.read(configFile)
        self.MYMOVIEDIR = config.get('mbMovieProcConfig', 'MYMOVIEDIR')
        self.TMDB_API = config.get('mbMovieProcConfig', 'TMDB_API')
        self.MOVIE_NAME_FORMAT = config.get('mbMovieProcConfig', 'MOVIE_NAME_FORMAT')
        self.WRITE_MB_MOVIE_XML = config.getint('mbMovieProcConfig', 'WRITE_MB_MOVIE_XML')
        self.WRITE_BOXEE_MOVIE_NFO = config.getint('mbMovieProcConfig', 'WRITE_BOXEE_MOVIE_NFO')
        self.MAX_BACKDROP = config.getint('mbMovieProcConfig', 'MAX_BACKDROP')
        self.KEEP_ORIG = config.getint('mbMovieProcConfig', 'KEEP_ORIG')
        self.MIN_RATIO = config.getfloat('mbMovieProcConfig', 'MIN_RATIO')
    
    def process(self, jobFolder):
        movieFiles = self.clean_folder_and_find_movie_files(jobFolder)
        finalMovieFile = self.join_and_get_final_movie_file(movieFiles)
        movieFilePart = os.path.basename(finalMovieFile)
        moviePathPart = os.path.dirname(finalMovieFile)
        movieExtension = movieFilePart[-4:]
        
        (cleanMovieName, movieYear) = self.get_clean_movie_name_from_tokens(movieFilePart)
        if cleanMovieName is None or movieYear is None:
            raise Exception("Can't continue without a clean movie namei and year")
            
        (theMovieObject, theTMDBMovieObject) = self.lookup_from_clean_name(cleanMovieName, movieYear)
        if theMovieObject is None or theTMDBMovieObject is None:
            raise Exception("Can't continue without movie objects")
            
        print "Matched movie.  Starting file operations..."
        cleanMovieName = theMovieObject['title']
        formattedMovieName = self.MOVIE_NAME_FORMAT.format(name=cleanMovieName, year=str(movieYear))
        newMovieFolder = self.MYMOVIEDIR + formattedMovieName
        newMoviePath = os.path.join(newMovieFolder, formattedMovieName + movieExtension)
        newMovieRename = os.path.join(moviePathPart, formattedMovieName + movieExtension)

        if os.path.exists(newMovieFolder):
            raise Exception("The new movie folder already exists")
    
        if self.KEEP_ORIG:
            print "Making new folder:", newMovieFolder
            os.mkdir(newMovieFolder)
            print "Copying movie file:", newMoviePath
            shutil.copy2(finalMovieFile, newMoviePath)
        else:
            print "Renaming Video file"
            os.rename(finalMovieFile, newMovieRename)
            print "Renaming Folder"
            os.rename(moviePathPart, newMovieFolder)

        print "Creating metadata..."
        self.write_meta_data(newMovieFolder, theMovieObject, theTMDBMovieObject)

        print "Done with metadata. Trying artwork..."
        self.write_artwork_from_tmdb(newMovieFolder, theTMDBMovieObject)

    def write_artwork_from_tmdb(self, newMovieFolder, theTMDBMovieObject):
        try:
            currBackdrop = 0
            for backdropUrl in theTMDBMovieObject.get_backdrop_list():
                backdropUrlExtension = backdropUrl[-4:]
                backdropUrlObject = urllib2.urlopen(backdropUrl)
                backdropData = backdropUrlObject.read()
                backdropUrlObject.close()
                backdropFileNamePart = "backdrop"
                if currBackdrop > 0:
                    backdropFileNamePart += str(currBackdrop)
                backdropFileNamePart += backdropUrlExtension
                print "Writing", backdropFileNamePart
                backdropFileName = os.path.join(newMovieFolder, backdropFileNamePart)
                backdropFile = open(backdropFileName, 'w')
                backdropFile.write(backdropData)
                backdropFile.close()
                currBackdrop += 1
                if currBackdrop >= self.MAX_BACKDROP:
                    break

            posterUrl = theTMDBMovieObject.get_poster()
            posterUrlExtension = posterUrl[-4:]
            posterUrlObject = urllib2.urlopen(posterUrl)
            posterData = posterUrlObject.read()
            posterUrlObject.close()
            posterFilename = os.path.join(newMovieFolder, "folder" + posterUrlExtension)
            print "Writing folder image..."
            posterFile = open(posterFilename, 'w')
            posterFile.write(posterData)
            posterFile.close()
        except Exception, exc:
            raise Exception("There was a problem with artwork", exc)

    def write_meta_data(self, newMovieFolder, theMovieObject, theTMDBMovieObject):
        theTitle = ""
        theRating = ""
        theYear = ""
        theMpaa = ""
        theRuntime = ""
        theOutline = ""
        thePlot = ""

        theImdbId = 'tt' + str(theMovieObject.movieID)
        theTmdbId = str(theTMDBMovieObject.get_id())
        if theMovieObject.has_key('title'):
            theTitle = unicodedata.normalize('NFKD', theMovieObject['title']).encode('ascii','ignore')
        if theMovieObject.has_key('rating'):
            theRating = str(theMovieObject['rating'])
        if theMovieObject.has_key('year'):
            theYear = str(theMovieObject['year'])
        if theMovieObject.has_key('mpaa'):
            theMpaa = unicodedata.normalize('NFKD', theMovieObject['mpaa']).encode('ascii','ignore')
        if theMovieObject.has_key('runtimes'):
            for rt in theMovieObject['runtimes']:
                if rt.isdigit():
                    theRuntime = rt
                    break
                if rt.startswith("USA"):
                    theRuntime = rt[4:]
                    break
        if theMovieObject.has_key('plot outline'):
            theOutline = unicodedata.normalize('NFKD', theMovieObject['plot outline']).encode('ascii','ignore')
        thePlot = theOutline

        if self.WRITE_MB_MOVIE_XML:
            theXMLFileName = os.path.join(newMovieFolder, "movie.xml")
            theXMLFile = open(theXMLFileName, 'w')
            theXMLFile.write('<?xml version="1.0" encoding="utf-8"?>\n');
            theXMLFile.write('<Title>\n')
            theXMLFile.write('    <LocalTitle>' + theTitle + '</LocalTitle>\n')
            theXMLFile.write('    <OriginalTitle>' + theTitle + '</OriginalTitle>\n')
            theXMLFile.write('    <SortTitle>' + theTitle + '</SortTitle>\n')
            theXMLFile.write('    <IMDBrating>' + theRating + '</IMDBrating>\n')
            theXMLFile.write('    <ProductionYear>' + theYear + '</ProductionYear>\n')
            theXMLFile.write('    <MPAARating>' + theMpaa + '</MPAARating>\n')
            theXMLFile.write('    <IMDbId>' + theImdbId + '</IMDbId>\n')
            theXMLFile.write('    <RunningTime>' + theRuntime + '</RunningTime>\n')
            theXMLFile.write('    <TMDbId>' + theTmdbId + '</TMDbId>\n')
            theXMLFile.write('    <CDUniverseId></CDUniverseId>\n')
            theXMLFile.write('    <Language>English</Language>\n')
            theXMLFile.write('    <Country>USA</Country>\n')
            theXMLFile.write('    <IMDB>' + theImdbId + '</IMDB>\n')
            theXMLFile.write('    <Added></Added>\n')
            theXMLFile.write('    <Budget></Budget>\n')
            theXMLFile.write('    <Revenue></Revenue>\n')
            theXMLFile.write('    <Description>' + theOutline + '</Description>\n')
    
            theXMLFile.write('    <Genres>\n')
            if theMovieObject.has_key('genres'):
                for gen in theMovieObject['genres']:
                    theXMLFile.write('        <Genre>' + str(gen) + '</Genre>\n')
            theXMLFile.write('    </Genres>\n')
            
            theXMLFile.write('    <Persons>\n')
            for person in theMovieObject['cast']:
                theName = unicodedata.normalize('NFKD', person['name']).encode('ascii','ignore')
                theRole = str(person.currentRole)

                theXMLFile.write('        <Person>\n')
                theXMLFile.write('            <Name>' + theName + '</Name>\n')
                theXMLFile.write('            <Type>Actor</Type>\n')
                theXMLFile.write('            <Role>' + theRole + '</Role>\n')
                theXMLFile.write('        </Person>\n')
            for person in theMovieObject['writer']:
                theName = unicodedata.normalize('NFKD', person['name']).encode('ascii','ignore')

                theXMLFile.write('        <Person>\n')
                theXMLFile.write('            <Name>' + theName + '</Name>\n')
                theXMLFile.write('            <Type>Writer</Type>\n')
                theXMLFile.write('            <Role></Role>\n')
                theXMLFile.write('        </Person>\n')
            for person in theMovieObject['director']:
                theName = unicodedata.normalize('NFKD', person['name']).encode('ascii','ignore')

                theXMLFile.write('        <Person>\n')
                theXMLFile.write('            <Name>' + theName + '</Name>\n')
                theXMLFile.write('            <Type>Director</Type>\n')
                theXMLFile.write('            <Role></Role>\n')
                theXMLFile.write('        </Person>\n')
            theXMLFile.write('    </Persons>\n')
            theXMLFile.write('    <Synopsis>' + thePlot + '</Synopsis>\n')
            theXMLFile.write('    <Plot>' + thePlot + '</Plot>\n')
            theXMLFile.write('    <Outline>' + thePlot + '</Outline>\n')
            theXMLFile.write('</Title>\n')
            theXMLFile.close();

        if self.WRITE_BOXEE_MOVIE_NFO:
            theNFOFileName = os.path.join(newMovieFolder, "movie.nfo")
            theNFOFile = open(theNFOFileName, 'w')
            theNFOFile.write('<?xml version="1.0" encoding="utf-8"?>\n');
            theNFOFile.write('<movie>\n')
            theNFOFile.write('    <title>' + theTitle + '</title>\n')
            theNFOFile.write('    <originaltitle>' + theTitle + '</originaltitle>\n')
            theNFOFile.write('    <sorttitle>' + theTitle + '</sorttitle>\n')
            theNFOFile.write('    <rating>' + theRating + '</rating>\n')
            theNFOFile.write('    <year>' + theYear + '</year>\n')
            theNFOFile.write('    <outline>' + thePlot + '</outline>\n')
            theNFOFile.write('    <plot>' + thePlot + '</plot>\n')
            theNFOFile.write('    <runtime>' + theRuntime + 'min</runtime>\n')
            theNFOFile.write('    <mpaa>' + theMpaa + '</mpaa>\n')
    
            theNFOFile.write('    <genre>')
            if theMovieObject.has_key('genres'):
                for gen in theMovieObject['genres']:
                    theNFOFile.write(str(gen) + ", ")
            theNFOFile.write('</genre>\n')
    
            for person in theMovieObject['director']:
                theName = unicodedata.normalize('NFKD', person['name']).encode('ascii','ignore')
                theNFOFile.write('    <director>' + theName + '</director>\n')
    
            for person in theMovieObject['cast']:
                theName = unicodedata.normalize('NFKD', person['name']).encode('ascii','ignore')
                theRole = str(person.currentRole)

                theNFOFile.write('    <actor>\n')
                theNFOFile.write('        <name>' + theName + '</name>\n')
                theNFOFile.write('        <role>' + theRole + '</role>\n')
                theNFOFile.write('    </actor>\n')
    
            theNFOFile.write('</movie>\n')
            theNFOFile.close();        
        
    def lookup_from_clean_name(self, cleanMovieName, movieYear):
        theMovieObject = None
        theTMDBMovieObject = None

        numRetries = 3
        currentTry = 1
        allSet = 0

        while allSet == 0 and currentTry < numRetries:
            try:
                isMovieMatched = 0
                print "Trying IMDB search, try number", str(currentTry)
                ia = imdb.IMDb(accessSystem='http')
                movies = ia.search_movie(cleanMovieName)
                print "IMDB Search returned", str(len(movies)), "movies"
                for movie in movies:
                    thisMovieTitle = movie['title']
                    ratio = difflib.SequenceMatcher(None, cleanMovieName, thisMovieTitle).quick_ratio()
                    if ratio < self.MIN_RATIO:
                        print "Movie \'", thisMovieTitle, "\' did not meet minimum difference ratio of", str(self.MIN_RATIO), "(", ratio, ")"
                        continue
    
                    if movie['kind'] == 'movie' and movie['year'] == movieYear:
                        currentTryInner = 1
                        allSetInner = 0
                        while allSetInner == 0 and currentTryInner < numRetries:
                            try:
                                ia.update(movie)
                                allSetInner = 1
                            except:
                                if currentTryInner < numRetries:
                                    print "Updating full movie from IMDB failed, retrying..."
                            currentTryInner += 1

                        isMovieMatched = 1
                        theMovieObject = movie
                        break
                    else:
                        print "Movie \'", thisMovieTitle, "\' did not match the media type and year of our movie"
    
                if not isMovieMatched:
                    raise Exception("Didnt find the movie on IMDB. Sad face.")
    
                isMovieMatched = 0
                print "Trying TMDB search..."
                theIMDBMovieTitle = theMovieObject['title']
                tmdb.configure(self.TMDB_API)
                movies = tmdb.Movies(theIMDBMovieTitle)
                print "TMDB returned", str(movies.get_total_results()), "movies"
                for movie in movies:
                    relDate = movie.get_release_date()
                    relDate = int(relDate[:4])
                    thisIMDBId = movie.get_imdb_id()
                    if relDate == movieYear and thisIMDBId == 'tt' + theMovieObject.movieID:
                        theTMDBMovieObject = movie
                        isMovieMatched = 1
                        break;
                        
                if not isMovieMatched:
                    raise Exception("Didnt find the movie on TMDB. Sad face.")
    
                allSet = 1
            except Exception, exc:
                if currentTry < numRetries:
                    print "Something went wrong with search..."
                    print str(exc)
                    print "Trying again..."
                else:
                    raise

            currentTry += 1

        return (theMovieObject, theTMDBMovieObject)
    
        
    def get_clean_movie_name_from_tokens(self, movieFilePart):
        tokens = re.split(' |,|\.|-|\(|\)', movieFilePart)

        #TODO: remove debug statements
        for token in tokens:
           print "Found token:", token

        #find the year
        movieYear = 0
        yearPosition = 0
        for token in tokens:
            if len(token) == 4 and token.isdigit():
                movieYear = int(token)
                break
            yearPosition += 1
            
        if movieYear == 0:
            print "Did not find a year"
            raise Exception("Cant continue, no year found in name")
        else:
            print "Movie year is:", str(movieYear)

        #use everything before the year as the name
        cleanMovieName = ""
        namePosition = 0
        for token in tokens:
            cleanMovieName += token + " "
            if namePosition >= yearPosition - 1:
                break
            namePosition += 1

        cleanMovieName = cleanMovieName.strip()
        print "Cleaned Movie Name:", cleanMovieName
        return (cleanMovieName, movieYear)
        
    def join_and_get_final_movie_file(self, movieFiles = []):
        if len(movieFiles) == 0:
            raise Exception("Did not find any movie files")

        if len(movieFiles) > 2:
            raise Exception("Currently can't join more than 2 files")
            
        finalMovieFile = movieFiles[0]
        if len(movieFiles) > 1:
            print "Two movie files, attempting join..."
            diff_blocks = difflib.SequenceMatcher(None, movieFiles[0], movieFiles[1]).get_matching_blocks()
            firstPartLength = diff_blocks[0][2]
            secondPartStarts = diff_blocks[1][0]
            fileExtension = movieFiles[0][-4:]
            if secondPartStarts != firstPartLength + 1:
                print "These files seem to differ before a \'CD1\' sort of indicator. Aborting..."
                raise Exception("Couldnt join, no CD indicator found")
                
            newFileName = movieFiles[0][:firstPartLength] + fileExtension
            mencoder_cmd_line = "mencoder -forceidx -ovc copy -oac copy -o \"" + newFileName + "\" \"" + movieFiles[0]
            mencoder_cmd_line += "\" \"" + movieFiles[1] + "\""
            print "Executing:", mencoder_cmd_line
            mencoder_ret_code = os.system(mencoder_cmd_line)
            finalMovieFile = newFileName
            print "Done joining. retcode:", str(mencoder_ret_code)
            
        return finalMovieFile
    
    def clean_folder_and_find_movie_files(self, jobFolder):
        allFiles = []

        for path,dirs,files in os.walk(jobFolder):
            for fn in files:
                allFiles.append(os.path.join(path,fn));

        print "Starting folder scan, keep original files is set to:", self.KEEP_ORIG

        movieFiles = []
        allFiles.sort()
        for file in allFiles:
            if file.endswith(".mkv") or file.endswith(".avi") or file.endswith(".mp4") or file.endswith(".mpg"):
                if file.find("sample") >= 0:
                    if not self.KEEP_ORIG:
                        print "Deleting sample:", file
                        os.remove(file)
                else:
                    print "Found movie file:", file
                    movieFiles.append(file)
            else:
                if not self.KEEP_ORIG:
                    print "Deleting non-movie file:", file
                    os.remove(file)

        return movieFiles
