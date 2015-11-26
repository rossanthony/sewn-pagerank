import math         # used for sqrt method
import numpy as np  # used for matrix data type
import json         # used to output data in json format for legibility
import urllib       # used to normalise URLs, with the unquote method (i.e. convert %7e to ~)
from urlparse import urljoin # allows conversion of relative urls into absolute ones 

class PageRank(object):

    def __init__(self):
        # Data structures
        self.visitedPages = []
        self.linksOnPages = {}
        self.crawledPages  = {} # holds Crawled Pages (read in from file)
        # Constants 
        self.totalOutlinks = 0
        self.teleportationFactor = 1.00
        self.convergence = 0.0001 
        self.dp = 4 # decimal places to round PR's to
        self.maxIterations = 100

        self.readInCrawlTxt()
        self.buildMatrix()
        self.saveMatrixAsCsv()
        self.calcTotals()
        self.initPageRanks()
        self.calcPageRanks()
        self.outputStats()
        self.saveOutput()
        # print json.dumps(self.linksOnPages, sort_keys=True, indent=4)

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
                    visited = urllib.unquote(line[9:].strip().rstrip('/')).lower()
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


    # Initialise the pageRanks, set them all to 1.
    #
    # Returns: Bool
    #
    def initPageRanks(self):
        # initialise PR values to 1
        self.stats = "Teleportation factor: %.2f\n" % self.teleportationFactor
        self.stats += "Convergence threashold: +/-%.4f\n" % self.convergence
        self.pageRanks = {}
        for page in self.visitedPages:
            self.pageRanks[page] = [1]
            
    
    # Main method handling the PageRank calculations
    #
    # Returns: Bool
    #  
    def calcPageRanks(self):
        iteration = 0
        convergedCount = 0

        while convergedCount < len(self.visitedPages) and iteration < self.maxIterations:
            iteration+=1
            totalPagerank = 0.0

            for page in self.visitedPages:
                inlinks = self.inlinks[page]
                outlinks = self.linksOnPages[page]

                pageRanksOfInlinks = []
                for link in inlinks:
                    pageRanksOfInlinks.append( self.pageRanks[link][iteration-1] / self.outlinkCounts[link] )

                # add inlinks for dangling pages to all pageranks
                for pageUrl, linksOnPage in self.linksOnPages.items():
                    if len(linksOnPage) == 0:
                        pageRanksOfInlinks.append( self.pageRanks[pageUrl][iteration-1] / len(self.visitedPages))

                # random surfer version of PR algorithm
                rank = self.teleportationFactor / len(self.visitedPages) + (1 - self.teleportationFactor) * sum(pageRanksOfInlinks)
                
                self.pageRanks[page].append(round(rank, self.dp))    
                totalPagerank = totalPagerank + rank
            
            # check for convergence
            convergedCount = 0
            for page in self.visitedPages:
                if self.pageRanks[page][iteration] >= self.pageRanks[page][iteration-1] - self.convergence:
                    convergedCount+=1
                # else:
                #     print "Iteration = %d, page %s not converged" % (iteration, page)

        self.stats += "Reached full convergence in %d iterations\n" % iteration
        self.addSumofPRsToStats(iteration)
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
        self.stats += "\nTotal (unique) visited pages: %d (of which %d are dangling)" % (len(self.visitedPages), len(self.visitedPages) - self.nonDanglingPages)
        self.stats += "\nTotal number of inlinks: %d | outlinks: %d\n" % (self.totalInlinks, self.totalOutlinks)
        
        # a) The number of inlinks to each page.
        self.stats += "\na) The number of inlinks to each page.\n\tSaved to: inlinksPerPage.txt\n"
        crawlerFile = open('inlinksPerPage.txt', "w")
        inlinksPerPage = "# inlinks per page\n"
        degreeDistInlinks = []
        for key, value in sorted(self.inlinkCounts.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            inlinksPerPage += "%d\t%s\n" % (value, key)
            degreeDistInlinks.append(value)
        crawlerFile.write(inlinksPerPage)
        crawlerFile.close()
    
        # b) The number of outlinks from each page.
        self.stats += "\nb) The number of outlinks to each page.\n\tSaved to: outlinksPerPage.txt\n"
        crawlerFile = open('outlinksPerPage.txt', "w")
        outlinksPerPage = "# outlinks per page\n"
        degreeDistOutlinks = []
        for key, value in sorted(self.outlinkCounts.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            outlinksPerPage += "%d\t%s\n" % (value, key)
            degreeDistOutlinks.append(value)

        crawlerFile.write(outlinksPerPage)
        crawlerFile.close()

        degreeDistInlinksDict = {}
        for numLinks in degreeDistInlinks:
            degreeDistInlinksDict[numLinks] = 0
        for numLinks in degreeDistInlinks:
            degreeDistInlinksDict[numLinks] = degreeDistInlinksDict[numLinks] + 1
        degreeDistInlinksOutput = "# inlinks\t# pages\n"
        for key, value in sorted(degreeDistInlinksDict.iteritems(), key=lambda t: t[0], reverse=True):
            degreeDistInlinksOutput += "%s\t\t\t%s\n" % (key, value)
        degreeDistInlinksFile = open('degreeDistInlinks.txt', "w")
        degreeDistInlinksFile.write(degreeDistInlinksOutput)
        degreeDistInlinksFile.close()

        degreeDistOutlinksDict = {}
        for numLinks in degreeDistOutlinks:
            degreeDistOutlinksDict[numLinks] = 0
        for numLinks in degreeDistOutlinks:
            degreeDistOutlinksDict[numLinks] = degreeDistOutlinksDict[numLinks] + 1
        degreeDistOutlinksOutput = "# outlinks\t# pages\n"
        for key, value in sorted(degreeDistOutlinksDict.iteritems(), key=lambda t: t[0], reverse=True):
            degreeDistOutlinksOutput += "%s\t\t\t%s\n" % (key, value)

        degreeDistOutlinksFile = open('degreeDistOutlinks.txt', "w")
        degreeDistOutlinksFile.write(degreeDistOutlinksOutput)
        degreeDistOutlinksFile.close()

        # c) The average (mean) number of inlinks to a page, variance and the standard deviation.
        self.stats += "\nc,d) The average (mean) number of in/outlinks to/from a page, variance and the standard deviation.\n"
        # d) The average (mean) number of outlinks from a page, variance and the standard deviation.
        self.stats += "\tMean number of inlinks: %d | outlinks: %d\n" % (int(self.totalInlinks) / int(len(self.visitedPages)), int(self.totalOutlinks) / int(len(self.visitedPages)))
        self.stats += "\tMean number of inlinks: %d | outlinks: %d\n" % (int(self.totalInlinks) / int(len(self.visitedPages)), int(self.totalOutlinks) / int(len(self.visitedPages)))
        
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

        self.stats += "\tVariance of inlinks: %d | outlinks: %d\n" % (inlinkVariance, outlinkVariance)
        self.stats += "\tStandard deviation of inlinks: %d | outlinks: %d\n" % (math.sqrt(inlinkVariance), math.sqrt(outlinkVariance))

        # e) The degree distribution of inlinks and outlinks, i.e. tables such as the following:
        self.stats += "\ne) The degree distribution of inlinks and outlinks.\n"
        self.stats += "\tDegree distribution has been saved to: degreeDistInlinks.txt, degreeDistOutlinks.txt\n"
        
        print self.stats
        

    
    def addSumofPRsToStats(self, iteration):
        totalPagerank = 0.0
        for page in self.visitedPages:
            totalPagerank = totalPagerank + self.pageRanks[page][iteration]
        self.stats += "Sum of all pageranks: %.4f\n" % totalPagerank


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
        filename = "statistics%.2f" % self.teleportationFactor
        filename = filename.replace('.','') + ".txt"
        crawlerFile = open(filename, "w")
        crawlerFile.write(str(self.stats))
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