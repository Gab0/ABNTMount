#!/bin/python
import yaml
import shutil
import re
import optparse
import os
import json
import itertools
import numpy as np

from ABNTMount import pdfFilter, citationInfo, runLatex, texFileParser

parser = optparse.OptionParser()

parser.add_option('-i', "--input",
                  dest='DefinitionsFile', help='Path to .yaml project file.')

parser.add_option('-d', dest='debugMode',
                  action='store_true', default=False)

parser.add_option('--norefs',
                  dest='linkReferences',
                  action='store_false',
                  default=True)

parser.add_option('--sc',
                  dest='skipCover',
                  action="store_true")

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


def generateManuscriptSequence(ManuscriptDirectory, SequenceGuide):
    Sequence = []
    listOfFiles = os.listdir(ManuscriptDirectory)

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


def parseManuscriptReferences(WorkingDirectory,
                              Manuscript, ArticleCache, projectDefinitions):

    CitationCommands = [
        "cite",
        "citeonline",
        "footfullcite"
    ]
    if "Citation" in projectDefinitions.keys():
        for c, Citation in enumerate(projectDefinitions["Citation"]):
            CitationCommands[c] = Citation

    searchPattern = "<*V*\[\[[\w./-]+\]\]"
    ArticleText = re.findall(searchPattern, Manuscript)
    ArticleIds = [x.strip("<V[]") for x in ArticleText]

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
            WorkingDirectory,
            MissingArticles,
            Verbose=True)
    else:
        MissingArticleResults = []

    # Update ArticleCache;
    for A in MissingArticleResults:
        ArticleCache[A["IDs"][0]] = A

    # Build article info results from Cache and from remote PUBMED;
    ArticleInfoResults = []
    DummyInfoResults = []
    for ArticleId in ArticleIds:
        onMissing = [
            A for A in MissingArticleResults
            if ArticleId in A["IDs"]
        ]
        if ArticleId in ArticleCache.keys():
            ArticleInfoResults.append(ArticleCache[ArticleId])
        elif onMissing:
            ArticleInfoResults.append(onMissing[0])
        else:
            DummyInfoResults.append({"IDs": [ArticleId]})

    articleTextIds = zip(ArticleText, ArticleIds)
    for TEXT in articleTextIds:
        print("%s\t%s" % (TEXT[0], TEXT[1]))

    print("Expanding References %i/%i" % (len(ArticleInfoResults),
                                          len(ArticleIds)))

    for z in range(len(ArticleText)):
        Found = False
        for AINFO in ArticleInfoResults + DummyInfoResults:
            if ArticleIds[z] in AINFO['IDs']:

                if "<" in ArticleText[z]:
                    TexCommand = '\%s' % CitationCommands[1]
                elif "V" in ArticleText[z]:
                    TexCommand = '\%s' % CitationCommands[2]
                else:
                    TexCommand = '\%s' % CitationCommands[0]

                TexCommand += "{%s}"

                Replacement = TexCommand % AINFO['IDs'][0]
                Manuscript = Manuscript.replace(ArticleText[z],
                                                Replacement, 1)
                Found = True
                break

        if not Found:
            notFound.append(ArticleIds[z])
            print("NOT FOUND %s" % ArticleIds[z])

    Manuscript += "\clearpage"

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
            if os.path.isfile(Path):
                Target = os.path.join(TempPath, F)
                shutil.copy2(Path, Target)


def main():
    # -- Load Project Definitions;
    if not os.path.isfile(options.DefinitionsFile):
        print(".yaml project definitions file not found.")

    ExternalFiles = {
        "DefinitionsFile": "Sequence.yaml",
        "UserBIBEntries": "baseBibtex.bib",
        "UserCSVArticles": "preloadedArticleInfo.csv"
    }

    projectDefinitions = yaml.load(open(options.DefinitionsFile).read())

    ManuscriptDirectory = os.path.dirname(
        os.path.realpath(options.DefinitionsFile)
    )

    # Load segment data from definitions file;
    segmentNames = ["Textual", "Pretextual"]
    segmentSequences = []
    segmentParts = []

    for segmentName in segmentNames:
        sequences = []
        parts = []
        if segmentName in projectDefinitions.keys():
            sequences = generateManuscriptSequence(
                ManuscriptDirectory,
                projectDefinitions[segmentName]
            )
            partsKey = segmentName + "Parts"
            if partsKey in projectDefinitions.keys():
                parts = projectDefinitions[partsKey]
        segmentSequences.append(sequences)
        segmentParts.append(parts)

    if options.debugMode:
        print(json.dumps(segmentSequences, indent=2))
        input()

    # Manage temporary files folder;
    TEMPFolderName = "ABNTMTemp"
    TempPath = os.path.join(ManuscriptDirectory, TEMPFolderName)

    texFileName = projectDefinitions["BaseTex"]
    texFilePath = os.path.join(ManuscriptDirectory,
                               texFileName)

    mainFileName = ''.join(texFileName.split('.')[:-1])
    pdfOutputName = "%s.pdf" % mainFileName

    if os.path.isdir(TempPath):
        shutil.rmtree(TempPath)

    os.mkdir(TempPath)

    assert(os.path.isfile(texFilePath))
    ArticleList = []

    # Copy Tables;
    if "Files" in projectDefinitions.keys():
        FileSpecifiers = projectDefinitions["Files"]
        for FileSpecifier in FileSpecifiers:
            if FileSpecifier.startswith("*"):
                copyProjectFiles(ManuscriptDirectory,
                                 TempPath, "", [FileSpecifier.strip("*")])
            else:
                copyProjectFiles(ManuscriptDirectory, TempPath, FileSpecifier)


    # PROCESS SEQUENCE;
    articlesNotFound = []

    # Load article cache filepath;
    ArticleCacheFilepath = os.path.join(ManuscriptDirectory,
                                        "ArticleCache.json")
    if os.path.isfile(ArticleCacheFilepath):
        with open(ArticleCacheFilepath) as f:
            ArticleCache = json.load(f)
    else:
        ArticleCache = {}

    allContentFiles = [[texFileName]] + segmentSequences
    print(allContentFiles)
    for FileName in itertools.chain(*allContentFiles):
        Manuscript = open("%s/%s" % (ManuscriptDirectory, FileName)).read()
        print('Parsing file %s' % FileName)
        if options.linkReferences:
            Manuscript, CitationData, notFound =\
                parseManuscriptReferences(ManuscriptDirectory,
                                          Manuscript,
                                          ArticleCache,
                                          projectDefinitions)
            articlesNotFound += notFound
        else:
            CitationData = []

        ArticleList += CitationData

        outputPath = TempPath + '/' + FileName
        if options.debugMode:
            print("%s -> %s" % (FileName, outputPath))

        output = open(outputPath, 'w')
        output.write(Manuscript)
        output.close()
        print("\n\n")

    json.dump(ArticleCache,
              open(ArticleCacheFilepath, 'w'),
              indent=2,
              cls=CacheEncoder)
    if options.debugMode:
        input()

    # -- BUILD BIBTEX CITAITON INFO;
    BIBFile = [runLatex.makeBibEntry(A) for A in ArticleList]
    BIBFile = '\n\n'.join(BIBFile)

    # -- parse base bib info;
    BaseBIBPath = os.path.join(ManuscriptDirectory, "baseBibtex.bib")
    if os.path.isfile(BaseBIBPath):
        BaseBIBFile = open(BaseBIBPath).read() + "\n\n"
        BIBFile = BaseBIBFile + BIBFile

    if "BIBFile" in projectDefinitions.keys():
        BIBFileName = projectDefinitions["BIBFile"]
    else:
        BIBFileName = "references.bib"
    BIBFilePath = os.path.join(TempPath, BIBFileName)
    open(BIBFilePath, 'w').write(BIBFile)

    # -- Parse and write tex file;
    replacementTokens = [
        "%<<CHAPTER-CONTENT>>",
        "%<<PRETEXTUAL-CONTENT>>"
    ]

    TempTexFilePath = os.path.join(TempPath, texFileName)
    texFileData = texFileParser.parseTexFile(TempTexFilePath,
                                             segmentSequences,
                                             replacementTokens,
                                             segmentParts)

    open(TempTexFilePath, 'w').write(texFileData)

    runLatex.runLatex(options,
                      os.path.join(TempPath, texFileName),
                      TempPath)

    TempOutput = os.path.join(TempPath, pdfOutputName)

    FinalOutput = os.path.join(ManuscriptDirectory, pdfOutputName)

    if options.skipCover:
        pdfFilter.fromPageContains(
            TempOutput,
            FinalOutput,
            'Resumo'
        )
    else:
        shutil.copy2(TempOutput, FinalOutput)

    if not options.debugMode:
        shutil.rmtree(TempPath)

    if articlesNotFound:
        print("\n\nARTICLE INFORMATION FAILURE FOR:")
        for A in articlesNotFound:
            print(A)


if __name__ == '__main__':
    main()
