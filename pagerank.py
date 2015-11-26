
from collections import OrderedDict
import math
import urllib
import numpy as np
import urlparse              # lib for parsing urls
from urlparse import urljoin # allows conversion of relative urls into absolute ones 
import json


class PageRank(object):

    def __init__(self):
        # Data structures
        self.visitedPages = []
        self.linksOnPages = {}
        self.crawledPages  = {} # holds Crawled Pages (read in from file)
        # Constants 
        self.totalOutlinks = 0
        self.teleportationFactor = 0.15
        self.convergence = 0.0001 
        self.dp = 4 # decimal places to round PR's to

        self.readInCrawlTxt()
        self.buildMatrix()
        self.saveMatrixAsCsv()
        self.calcTotals()
        self.initPageRanks()
        self.calcPageRanks()
        self.outputStats()
        self.saveOutput()

    #
    # Returns: Void
    #
    def calcTotals(self):
        rowTotals = self.matrix.sum(axis=1) # rows
        columnTotals = self.matrix.sum(axis=0) # cols
        self.inlinks = {}
        self.inlinkCounts = {}
        self.outlinkCounts = {}
        self.totalInlinks = 0
        self.totalOutlinks = 0
        index = 0
        for page in self.visitedPages:
            self.inlinks[page] = self.findAllPagesWithInlinksToUrl(page)
            self.inlinkCounts[page]  = columnTotals.item(index)
            self.outlinkCounts[page] = rowTotals[index].item(0)
            self.totalInlinks  += int(columnTotals.item(index))
            self.totalOutlinks += int(rowTotals[index].item(0))
            index+=1
        # Get the total num of non-dangling pages    
        self.nonDanglingPages = 0;
        for page, outlinks in self.linksOnPages.items():
            if len(outlinks) > 0:
                self.nonDanglingPages += 1


    def findAllPagesWithInlinksToUrl(self, searchFor):
        inlinksFound = []
        for page, linksOnPage in self.linksOnPages.items():
            if searchFor in linksOnPage:
                inlinksFound.append(page)
                # print page
                # print linksOnPage
        return inlinksFound


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
                    visited = urllib.unquote(line[9:].strip().rstrip('/'))
                    if self.isUniqueUrl(visited):
                        self.visitedPages.append(visited)
                        self.linksOnPages[visited] = []
                        addLinks = True
                    else:
                        addLinks = False
                if addLinks and line[:9] == '    Link:':
                    # print self.getAbsoluteUrl(visited, line[10:].strip())
                    self.linksOnPages[visited].append(self.getAbsoluteUrl(visited, line[10:].strip().rstrip('/')))
                    self.totalOutlinks+=1


    # Loop through all Crawled Pages and check for links to other Crawled Pages
    #
    # Returns: Bool
    #
    def buildMatrix(self):
        allPages = []
        for rowVisitedUrl in self.visitedPages:
            row = []
            for pageToCheck in self.visitedPages:
                if pageToCheck in self.linksOnPages[rowVisitedUrl]: row.append(1)
                else: row.append(0)
            allPages.append(row)
        self.matrix = np.matrix(allPages)


    def initPageRanks(self):
        # initialise PR values to 1
        self.stats = "Teleportation factor: %.2f\n" % self.teleportationFactor
        self.stats += "Convergence threashold: +/-%.4f\n" % self.convergence
        self.pageRanks = {}
        for page in self.visitedPages:
            self.pageRanks[page] = [1]
            
        
    def calcPageRanks(self):
        iteration = 0
        convergedCount = 0

        while convergedCount < len(self.visitedPages):
            iteration+=1
            totalPagerank = 0.0

            for page in self.visitedPages:
                inlinks = self.inlinks[page]
                outlinks = self.linksOnPages[page]

                if len(outlinks) > 0:
                    pageRanksOfInlinks = []
                    for link in inlinks:
                        pageRanksOfInlinks.append( self.pageRanks[link][iteration-1] / self.outlinkCounts[link] )

                    # random surfer version of PR algorithm
                    rank = self.teleportationFactor / self.nonDanglingPages + (1 - self.teleportationFactor) * sum(pageRanksOfInlinks)
                else:
                    # print "page %s has no outlinks" % page
                    # print "using previous rank: %f" % self.pageRanks[page][iteration-1]
                    rank = self.pageRanks[page][iteration-1]

                self.pageRanks[page].append(round(rank, self.dp))    
                totalPagerank = totalPagerank + rank
            
            # check for convergence
            convergedCount = 0
            for page in self.visitedPages:
                if self.pageRanks[page][iteration] >= self.pageRanks[page][iteration-1] - self.convergence:
                    convergedCount+=1
                # else:
                #     print "Iteration = %d, page %s not converged" % (iteration, page)

        self.stats += "Reached convergence of non-dangling pages in %d iterations\n" % iteration

        self.stats += "Now calculating PR's for the dangling pages...\n"
        convergedCount = 0

        while convergedCount < len(self.visitedPages):
            iteration+=1
            totalPagerank = 0.0

            for page in self.visitedPages:
                inlinks = self.inlinks[page]
                outlinks = self.linksOnPages[page]

                if len(outlinks) == 0:
                    pageRanksOfInlinks = []
                    for link in inlinks:
                        pageRanksOfInlinks.append( self.pageRanks[link][iteration-1] / self.outlinkCounts[link] )

                    # random surfer version of PR algorithm
                    rank = self.teleportationFactor / len(self.visitedPages) + (1 - self.teleportationFactor) * sum(pageRanksOfInlinks)
                else:
                    rank = self.pageRanks[page][iteration-1]

                self.pageRanks[page].append(round(rank, self.dp))    
                totalPagerank = totalPagerank + rank
            
            # check for convergence
            convergedCount = 0
            for page in self.visitedPages:
                if self.pageRanks[page][iteration] >= self.pageRanks[page][iteration-1] - self.convergence:
                    convergedCount+=1

        self.stats += "Reached full convergence in %d iterations\n" % iteration
        self.stats += "Done!\n...\n"

        filename = "pagerank%.2f_workings" % self.teleportationFactor
        filename = filename.replace('.','') + ".txt"
        self.stats += "PR iteration trace saved to: `%s`\n" % filename
        crawlerFile = open(filename, "w")
        crawlerFile.write(str(json.dumps(self.pageRanks, sort_keys=True, indent=4)))
        crawlerFile.close()

        finalPageRanks = {}
        for page in self.pageRanks:
            finalPageRanks[page] = self.pageRanks[page][iteration]

        filename = "pagerank%.2f" % self.teleportationFactor
        filename = filename.replace('.','') + ".txt"
        self.stats += "Final PR values saved to: `%s`\n" % filename
        crawlerFile = open(filename, "w")
        orderedPageRanks = "# iterations: %d\n" % iteration

        for key, value in sorted(finalPageRanks.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            orderedPageRanks += "\t%s\t%s\n" % (key, value)

        crawlerFile.write(orderedPageRanks)
        crawlerFile.close()
        # print json.dumps(finalPageRanks, sort_keys=True, indent=4)


    def outputStats(self):
        # a) The number of inlinks to each page.
        crawlerFile = open('inlinksPerPage.txt', "w")
        inlinksPerPage = "# inlinks per page\n"
        for key, value in sorted(self.inlinkCounts.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            inlinksPerPage += "%d\t%s\n" % (value, key)
        crawlerFile.write(inlinksPerPage)
        crawlerFile.close()
    
        # b) The number of outlinks from each page.
        crawlerFile = open('outlinksPerPage.txt', "w")
        outlinksPerPage = "# outlinks per page\n"
        for key, value in sorted(self.outlinkCounts.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            outlinksPerPage += "%d\t%s\n" % (value, key)
        crawlerFile.write(outlinksPerPage)
        crawlerFile.close()

        # c) The average (mean) number of inlinks to a page, variance and the standard deviation.
        # d) The average (mean) number of outlinks from a page, variance and the standard deviation.
        self.stats += "Total (unique) visited pages: %d (of which %d are dangling)\n" % (len(self.visitedPages), len(self.visitedPages) - self.nonDanglingPages)
        self.stats += "Total number of inlinks: %d | outlinks: %d\n" % (self.totalInlinks, self.totalOutlinks)
        self.stats += "Mean number of inlinks: %d | outlinks: %d\n" % (int(self.totalInlinks) / int(len(self.visitedPages)), int(self.totalOutlinks) / int(len(self.visitedPages)))
        self.stats += "Mean number of inlinks: %d | outlinks: %d\n" % (int(self.totalInlinks) / int(len(self.visitedPages)), int(self.totalOutlinks) / int(len(self.visitedPages)))
        
        # To calculate the variance follow these steps: 
        # Work out the Mean (the simple average of the numbers) 
        # Then for each number: subtract the Mean and square the result (the squared difference). 
        # Then work out the average of those squared differences.
        inlinkVariance = []
        for inlink, count in self.inlinkCounts.items():
            inlinkVariance.append((count - (int(self.totalInlinks) / int(len(self.visitedPages)))) * (count - (int(self.totalInlinks) / int(len(self.visitedPages)))))
        inlinkVariance = sum(inlinkVariance) / float(len(inlinkVariance))

        outlinkVariance = []
        for inlink, count in self.outlinkCounts.items():
            outlinkVariance.append((count - (int(self.totalOutlinks) / int(len(self.visitedPages)))) * (count - (int(self.totalOutlinks) / int(len(self.visitedPages)))))
        outlinkVariance = sum(outlinkVariance) / float(len(outlinkVariance))

        self.stats += "Variance of inlinks: %d | outlinks: %d\n" % (inlinkVariance, outlinkVariance)
        self.stats += "Standard deviation of inlinks: %d | outlinks: %d\n" % (math.sqrt(inlinkVariance), math.sqrt(outlinkVariance))

        # e) The degree distribution of inlinks and outlinks, i.e. tables such as the following:
        self.stats += "Degree of distribution saved to: inlinksPerPage.txt, outlinksPerPage.txt\n"
        
        print self.stats
        

    # Save the link matrix as a csv
    # 
    # Returns: String (url)
    #
    def saveMatrixAsCsv(self):
        index = 0
        csv = ' ,'
        for visitedUrl in self.visitedPages:
            csv += visitedUrl + ','
        csv += "\n"
        for visitedUrl in self.visitedPages:
            csv += visitedUrl + ','
            # print self.matrix[index].tolist().pop()
            for val in self.matrix[index].tolist().pop():
                csv +=  "%d," % val
            csv += "\n"
            index+=1
            
        csvMatrixFile = open("matrix.csv", "w")
        csvMatrixFile.write(str(csv))
        csvMatrixFile.close()


    # Convert a URL into absolute
    # 
    # Returns: String (url)
    #
    def getAbsoluteUrl(self, currentPageUrl, outlink):
        return urllib.unquote(urljoin(currentPageUrl, outlink).replace('/../', '/')).lower()


    # Check if a given url has already been stored
    #
    # Returns: Bool
    #
    def isUniqueUrl(self, url):
        for pageUrl in self.visitedPages:
            if pageUrl == url:
                return False
        return True


    def saveOutput(self):
        output = self.stats
        # for visitedUrl in self.visitedPages:
        #     output += "\"%s\": " % visitedUrl
        #     output += json.dumps(self.linksOnPages[visitedUrl], sort_keys=True, indent=4)
        #     output += ",\n"
        output += "\n"
        crawlerFile = open("output.txt", "w")
        crawlerFile.write(str(output))
        crawlerFile.close()
        return True


    def saveLinks(self):
        output = ''
        for pageUrl in self.visitedPages:
            output += "%s\n" % pageUrl
        crawlerFile = open("visited-pages.txt", "w")
        crawlerFile.write(str(output))
        crawlerFile.close()
        return True

PageRank()