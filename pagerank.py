
from collections import defaultdict # dictionary data structures
import numpy as np
import urlparse              # lib for parsing urls
from urlparse import urljoin # allows conversion of relative urls into absolute ones 
import json


class PageRank(object):

    def __init__(self):
        # Data structures
        self.crawledPages  = defaultdict(list)  # holds Crawled Pages (read in from file)
        self.totalOutlinks = 0

        self.readInCrawlTxt()
        #print self.matrix
        print json.dumps(self.crawledPages, sort_keys=True, indent=4)
        
        print "Total Visited Pages: %d" % len(self.crawledPages)
        print "Total Outlinks: %s" % self.totalOutlinks
        
        self.saveOutput()
        self.saveLinks()
        self.buildMatrix()
        print self.matrix


    #
    # Returns: Void
    #
    def readInCrawlTxt(self):
        addLinks = False
        with open("sewn-crawl-2015.txt", "r") as ifile:
            #print ifile.read()
            for line in ifile:
                if not line:
                    break
                if line[:8] == 'Visited:':
                    visited = line[9:].strip().rstrip('/')
                    if self.isStoredUrl(visited):
                        self.crawledPages[visited] = []
                        addLinks = True
                    else:
                        addLinks = False
                if addLinks and line[:9] == '    Link:':
                    self.crawledPages[visited].append(self.getAbsoluteUrl(visited, line[10:].strip()))
                    self.totalOutlinks+=1


    # Loop through all Crawled Pages and check for links to other Crawled Pages
    #
    # Returns: Bool
    #
    def buildMatrix(self):
        allPages = []
        for rowPage in self.crawledPages:
            row = []
            for pageToCheck in self.crawledPages:
                if pageToCheck in self.crawledPages[rowPage]: row.append(1)
                else: row.append(0)
            allPages.append(row)
        self.matrix = np.matrix(allPages)


    # Convert a URL into absolute
    # 
    # Returns: String (url)
    #
    def getAbsoluteUrl(self, currentPageUrl, outlink):
        return urljoin(currentPageUrl, outlink).replace('/../', '/')


    # Check if a given url has already been stored
    #
    # Returns: Bool
    #
    def isStoredUrl(self, url):
        for pageUrl in self.crawledPages:
            if pageUrl == url:
                return False
        return True


    def saveOutput(self):
        output = json.dumps(self.crawledPages, sort_keys=True, indent=4)
        crawlerFile = open("output.txt", "w")
        crawlerFile.write(str(output))
        crawlerFile.close()
        return True

    def saveLinks(self):
        output = ''
        for pageUrl in self.crawledPages:
            output += "%s\n" % pageUrl
        crawlerFile = open("visited-pages.txt", "w")
        crawlerFile.write(str(output))
        crawlerFile.close()
        return True



PageRank()