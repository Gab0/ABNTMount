#!/bin/python

import yaml
import shutil
import re
import optparse
import os
import json
import itertools
import numpy as np

from ABNTMount.Bibliography import bibParser
from ABNTMount.Output import pdfFilter, runLatex, renderBib
from ABNTMount import texFileParser


def parseArguments():
    parser = optparse.OptionParser()

    parser.add_option('-i', "--input",
                      dest='DefinitionsFile',
                      help='Path to .yaml project file.')

    parser.add_option('-d', dest='debugMode',
                      action='store_true', default=False)

    parser.add_option('--norefs',
                      dest='linkReferences',
                      action='store_false',
                      default=True)

    parser.add_option('--sc',
                      dest='skipCover',
                      action="store_true")

    parser.add_option('--bib',
                      dest="OnlyBib",
                      action='store_true')

    parser.add_option('--latex',
                      dest="LatexExecutable",
                      default='xelatex')
    """
    FIXME: CONFIGURABLE ON PROJECT DEFINITIONS
    parser.add_option("--base-bib",
                      dest="baseBibtex",
                      help="File path for a previously created bibfile.",
                      default="")
    """

    options, args = parser.parse_args()
    return options


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

    def extract_file_index(BaseName, fname):
        Q = re.findall(BaseName + r"([\d\.]+)_", fname)
        if Q:
            return float(Q[0])
        return None

    def search_numbered_files(listOfFiles, BaseName):
        ext = lambda x: extract_file_index(BaseName, x)

        validFiles = [f for f in listOfFiles if ext(f) is not None]
        for F in sorted(validFiles, key=ext):
            yield F
            #print(f"Warning! Repeated indexed file of BaseName{v}! Recheck your files.")

    for F in SequenceGuide:
        if '{*}' in F:
            BaseName = F.strip('{*}')
            Sequence += list(search_numbered_files(listOfFiles, BaseName))

        else:
            W = tryFile(F)
            if W:
                Sequence.append(W)
            else:
                print("File %s not found" % F)
                exit()

    return Sequence

def copyProjectFiles(workingDir, TempPath,
                     subdirectory, allowedExtensions=[], Verbose=True):

    def searchDirectory(workingDir, subdirectory):
        Path = os.path.join(workingDir, subdirectory)
        if os.path.isdir(Path):
            Files = os.listdir(Path)
            for File in Files:
                new_subdir = os.path.join(subdirectory, File)
                searchDirectory(workingDir, new_subdir)

        elif os.path.isfile(Path):
            if allowedExtensions:
                if os.path.splitext(Path)[-1] not in allowedExtensions:
                    return
            fname = os.path.split(Path)[-1]
            Target = os.path.join(TempPath, fname)
            if Verbose:
                print("Copying file %s to %s" % (Path, Target))
            shutil.copy2(Path, Target)

    if subdirectory.startswith("$"):
        subdirectory = subdirectory.strip("$")
        Source = os.path.join(workingDir, subdirectory)
        Target = os.path.join(TempPath, subdirectory)
        if Verbose:
            print("Copying tree %s to %s" % (Source, Target))

        shutil.copytree(Source, Target)

    else:
        searchDirectory(workingDir, subdirectory)


def makeBib(options):
    projectDefinitions = {
        "citation_pattern": "md"
    }

    Manuscript = open(options.DefinitionsFile).read()
    Manuscript, ArticleData, notFound =\
        bibParser.parseManuscriptReferences(
            ".",
            Manuscript,
            {},
            projectDefinitions
        )

    renderBib.renderBibtexFile("document.bib", None, None, ArticleData)


def main():
    options = parseArguments()
    if options.OnlyBib:
        makeBib(options)
    else:
        buildProjectWithDefinitions(options)


def buildProjectWithDefinitions(options):
    # -- Load Project Definitions;
    if not os.path.isfile(options.DefinitionsFile):
        print(".yaml project definitions file not found.")

    ExternalFiles = {
        "DefinitionsFile": "Sequence.yaml",
        "UserBIBEntries": "baseBibtex.bib",
        "UserCSVArticles": "preloadedArticleInfo.csv"
    }

    projectDefinitions = yaml.load(
        open(options.DefinitionsFile).read(),
        Loader=yaml.SafeLoader
    )

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

    texFiles = [
        f for f in os.listdir(ManuscriptDirectory)
        if f.endswith(".tex")
    ]

    # Copy all files used in the project;
    if "Files" in projectDefinitions.keys():
        FileSpecifiers = projectDefinitions["Files"] + texFiles
        for FileSpecifier in FileSpecifiers:
            if FileSpecifier.startswith("*"):
                copyProjectFiles(ManuscriptDirectory,
                                 TempPath, "", [FileSpecifier.strip("*")])
            else:
                copyProjectFiles(ManuscriptDirectory, TempPath, FileSpecifier)

    # PROCESS SEQUENCE;
    articlesNotFound = []
    ArticleList = []

    # Load article cache filepath;
    ArticleCacheFilepath = os.path.join(ManuscriptDirectory,
                                        "ArticleCache.json")
    if os.path.isfile(ArticleCacheFilepath):
        with open(ArticleCacheFilepath) as f:
            ArticleCache = json.load(f)
    else:
        ArticleCache = {}

    extraFiles = [
        f for f in os.listdir(TempPath)
        if f.endswith(".caption")
    ]

    allContentFiles = [[texFileName]] + segmentSequences + [extraFiles]

    print("Located content files:")
    for f in allContentFiles:
        print(f)

    for FileName in itertools.chain.from_iterable(allContentFiles):
        ManuscriptPath = os.path.join(TempPath, FileName)
        with open(ManuscriptPath) as mf:
            Manuscript = mf.read()
            print('Parsing file %s' % FileName)
            if options.linkReferences:
                Manuscript, CitationData, notFound =\
                    bibParser.parseManuscriptReferences(
                        ManuscriptDirectory,
                        Manuscript,
                        ArticleCache,
                        projectDefinitions
                    )
                articlesNotFound += notFound
            else:
                CitationData = []

        ArticleList += CitationData

        outputPath = TempPath + '/' + FileName
        if options.debugMode:
            print("%s -> %s" % (FileName, outputPath))

        with open(outputPath, 'w') as output:
            output.write(Manuscript)

        print("\n\n")

    json.dump(
        ArticleCache,
        open(ArticleCacheFilepath, 'w'),
        indent=2,
        cls=CacheEncoder,
        sort_keys=True
    )

    if options.debugMode:
        input()

    if "BIBFile" in projectDefinitions.keys():
        BIBFileName = projectDefinitions["BIBFile"]
    else:
        BIBFileName = "references.bib"

    BIBFilePath = os.path.join(TempPath, BIBFileName)

    BaseBIBFilePath = os.path.join(
        ManuscriptDirectory,
        ExternalFiles["UserBIBEntries"]
    )
    renderBib.renderBibtexFile(BIBFilePath,
                               BaseBIBFilePath,
                               ManuscriptDirectory,
                               ArticleList)
    
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
