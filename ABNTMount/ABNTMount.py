#!/bin/python
import yaml
import shutil
import re
import optparse
import os
import json
import numpy as np

from ABNTMount import pdfFilter, citationInfo, runLatex, texFileParser

parser = optparse.OptionParser()

parser.add_option('--dir <DIR>', dest='ManuscriptDir', default=os.getcwd())
parser.add_option('--name <NAME>', dest='texFileName', default='')
parser.add_option('-d', dest='debugMode',
                  action='store_true', default=False)
parser.add_option('--norefs',
                  dest='linkReferences',
                  action='store_false',
                  default=True)


options, args = parser.parse_args()


class CacheEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(CacheEncoder, self).default(obj)


def generateManuscriptSequence(SequenceGuide):
    Sequence = []
    listOfFiles = os.listdir(options.ManuscriptDir)

    def tryFile(TargetQueryName):
        for File in listOfFiles:
            if File.startswith(TargetQueryName):
                return File
        return None

    for F in SequenceGuide:
        if '{*}' in F:
            BaseName = F.strip('{*}')
            fail, K = 5, 0

            while fail > 0:
                K += 1
                count = 0
                TargetQueryName = BaseName + str(K) + "_"
                TargetName = tryFile(TargetQueryName)
                if TargetName:
                    count += 1

                if count > 1:
                    exit("Ambigous file list! Check manuscript folder.")
                elif count == 1:
                    Sequence.append(TargetName)
                else:
                    fail -= 1

        else:
            W = tryFile(F)
            if W:
                Sequence.append(W)
            else:
                print("File %s not found" % F)
                exit()

    return Sequence


def parseManuscriptReferences(Manuscript, ArticleCache):
    searchPattern = "<*\[\[[\w./-]+\]\]"
    ArticleText = re.findall(searchPattern, Manuscript)
    ArticleIds = [x.strip("<").strip("[").strip("]") for x in ArticleText]

    notFound = []
    if not ArticleIds:
        return Manuscript, [], []

    # Select missing article ids;
    MissingArticles = []
    for ArticleId in ArticleIds:
        if ArticleId not in ArticleCache.keys():
            MissingArticles.append(ArticleId)

    # Query missing article ids;
    if MissingArticles:
        print(MissingArticles)
        MissingArticleResults = citationInfo.getBatchCitationInfo(
            MissingArticles,
            Verbose=True)
    else:
        MissingArticleResults = []

    # Update ArticleCache;
    for A in MissingArticleResults:
        ArticleCache[A["IDs"][0]] = A

    # Build article info results from Cache and from remote PUBMED;
    ArticleInfoResults = []
    for ArticleId in ArticleIds:
        if ArticleId in ArticleCache.keys():
            ArticleInfoResults.append(ArticleCache[ArticleId])
        else:
            ArticleInfoResults.append([
                A for A in MissingArticleResults
                if ArticleId in A["IDs"]][0])

    articleTextIds = zip(ArticleText, ArticleIds)
    for TEXT in articleTextIds:
        print("%s\t%s" % (TEXT[0], TEXT[1]))
    print("Expanding References %i/%i" % (len(ArticleInfoResults),
                                          len(ArticleIds)))

    for z in range(len(ArticleText)):
        Found = False
        for AINFO in ArticleInfoResults:
            if ArticleIds[z] in AINFO['IDs']:
                if "<" in ArticleText[z]:
                    Replacement = '\citeonline{%s}' % AINFO['IDs'][0]
                else:
                    Replacement = '\cite{%s}' % AINFO['IDs'][0]
                    # print("< not in %s." % ArticleText[z])

                Manuscript = Manuscript.replace(ArticleText[z],
                                                Replacement, 1)
                Found = True
                break

        if not Found:
            notFound.append(ArticleIds[z])
            print("NOT FOUND %s" % ArticleIds[z])

    return Manuscript, ArticleInfoResults, notFound


def copyProjectFiles(workingDir, TempPath,
                     subdirectory, allowedExtensions=[]):

    subdirectoryPath = os.path.join(workingDir, subdirectory)
    if os.path.isdir(subdirectoryPath):
        Files = os.listdir(subdirectoryPath)
        for F in Files:
            if allowedExtensions:
                if os.path.splitext(F)[-1] not in allowedExtensions:
                    continue

            Path = os.path.join(subdirectoryPath, F)
            Target = os.path.join(TempPath, F)
            shutil.copy2(Path, Target)


def main():
    # -- Load Project Definitions;
    definitionsFilepath = os.path.join(options.ManuscriptDir, "Sequence.yaml")
    projectDefinitions = yaml.load(open(definitionsFilepath).read())

    [pretextualSequence, Sequence] = [
        generateManuscriptSequence(projectDefinitions[Attr])
        for Attr in ["Pretextual", "Textual"]
    ]

    TEMPFolderName = "ABNTMTemp"
    TempPath = os.path.join(options.ManuscriptDir, TEMPFolderName)

    mainFileName = ''.join(options.texFileName.split('.')[:-1])
    pdfOutputName = "%s.pdf" % mainFileName

    texFilePath = os.path.join(options.ManuscriptDir, options.texFileName)

    if os.path.isdir(TempPath):
        shutil.rmtree(TempPath)
    os.mkdir(TempPath)

    assert(os.path.isfile(texFilePath))
    ArticleList = []

    # Copy Tables;
    copyProjectFiles(options.ManuscriptDir, TempPath, "Tables", [".csv"])

    # Copy Figures;
    copyProjectFiles(options.ManuscriptDir, TempPath, "Figures")

    # PROCESS SEQUENCE;
    articlesNotFound = []

    # Load article cache filepath;
    ArticleCacheFilepath = os.path.join(options.ManuscriptDir,
                                        "ArticleCache.json")
    if os.path.isfile(ArticleCacheFilepath):
        with open(ArticleCacheFilepath) as f:
            ArticleCache = json.load(f)
    else:
        ArticleCache = {}

    for FileName in pretextualSequence + Sequence:
        Manuscript = open("%s/%s" % (options.ManuscriptDir, FileName)).read()
        print('Parsing file %s' % FileName)
        if options.linkReferences:
            Manuscript, CitationData, notFound =\
                parseManuscriptReferences(Manuscript, ArticleCache)
            articlesNotFound += notFound
        else:
            CitationData = []

        ArticleList += CitationData

        output = open(TempPath+'/'+FileName, 'w')
        output.write(Manuscript)
        print("\n\n")

    json.dump(ArticleCache,
              open(ArticleCacheFilepath, 'w'),
              indent=2,
              cls=CacheEncoder)

    BIBFile = [runLatex.makeBibEntry(A) for A in ArticleList]
    BIBFile = '\n\n'.join(BIBFile)
    open(TempPath+'/references.bib', 'w').write(BIBFile)

    # -- Parse and write tex file;
    texFileData = texFileParser.parseTexFile(texFilePath,
                                             pretextualSequence,
                                             Sequence,
                                             projectDefinitions["Parts"])

    open(os.path.join(TempPath, options.texFileName), 'w').write(texFileData)

    runLatex.runLatex(options,
                      os.path.join(TempPath, options.texFileName),
                      TempPath)

    pdfFilter.fromPageContains(
        os.path.join(TempPath, pdfOutputName),
        os.path.join(options.ManuscriptDir, pdfOutputName),
        'Resumo'
    )

    if not options.debugMode:
        shutil.rmtree(TempPath)

    if articlesNotFound:
        print("\n\nARTICLE INFORMATION FAILURE FOR:")
        for A in articlesNotFound:
            print(A)


if __name__ == '__main__':
    main()
