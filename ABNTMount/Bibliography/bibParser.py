
import re

from typing import List
from . import DOI, pubmed


def loadCitationCommands(projectDefinitions):
    CitationCommands = [
        "cite",
        "citeonline",
        "footfullcite"
    ]

    if "Citation" in projectDefinitions.keys():
        for c, Citation in enumerate(projectDefinitions["Citation"]):
            CitationCommands[c] = Citation

    return CitationCommands


def locateReferencePatterns(Manuscript: str, projectDefinitions):
    if "citation_pattern" in projectDefinitions.keys():
        Pattern = projectDefinitions["citation_pattern"]
    else:
        Pattern = "abntm"

    def ID(i):
        return i

    if Pattern == "abntm":
        searchPattern = r"<*V*\[\[[\w./-]+\]\]"
        searchStrip = "<V[ ]"

    elif Pattern == "md":
        searchPattern = r"<*\[@[@\w./-; ]+\]"
        searchStrip = "<[@ ]"

    def ArticleIDFromText(Text, searchStrip):
        IDs = Text.split(";")
        return [ID.strip(searchStrip) for ID in IDs]

    ReferencePatterns = re.findall(searchPattern, Manuscript)

    def flatten(x):
        print(x)
        return [item for sublist in x for item in sublist]

    ArticleIDs = flatten([ArticleIDFromText(Text, searchStrip)
                          for Text in ReferencePatterns])
    return ReferencePatterns, ArticleIDs


def downloadMissingArticleInformation(ArticleIDs: List[str],
                                      ArticleCache,
                                      WorkingDirectory: str):
    # Select missing article ids;
    MissingArticles = []
    for ArticleId in ArticleIDs:
        if ArticleId not in ArticleCache.keys():
            MissingArticles.append(ArticleId)

    # Query missing article ids;
    MissingArticleResults = []

    # Early return;
    if not MissingArticles:
        return []

    MA_DOI = [A for A in MissingArticles if "/" in A]
    if MA_DOI:
        MissingArticleResults += [DOI.getCitationInfo(A) for A in MA_DOI]

    MA_PUBMED = [A for A in MissingArticles if A not in MA_DOI]
    if MA_PUBMED:
        MissingArticleResults += pubmed.getBatchCitationInfo(
            WorkingDirectory,
            MA_PUBMED, Verbose=True
        )

    for A in MissingArticleResults:
        assert isinstance(A, tuple)
        assert len(A) == 2
    return MissingArticleResults


def parseManuscriptReferences(WorkingDirectory: str,
                              ManuscriptText: str,
                              ArticleCache,
                              projectDefinitions):

    ReferencePatterns, ArticleIDs =\
        locateReferencePatterns(ManuscriptText, projectDefinitions)

    notFound: List[str] = []

    if not ArticleIDs:
        return ManuscriptText, [], []

    MissingArticleResults =\
        downloadMissingArticleInformation(ArticleIDs,
                                          ArticleCache,
                                          WorkingDirectory)

    # Update ArticleCache;
    for ids, content in MissingArticleResults:
        assert isinstance(content, str)
        ArticleCache[ids[0]] = content

    # Build article info results from Cache and from remote PUBMED;
    ArticleInfoResults = []
    DummyInfoResults = []

    for ArticleId in ArticleIDs:
        onMissing = [
            A for A in MissingArticleResults
            if ArticleId in A[0]
        ]
        if ArticleId in ArticleCache.keys():
            ArticleInfoResults.append(ArticleCache[ArticleId])
        elif onMissing:
            ArticleInfoResults.append(onMissing[0][1])
        else:
            DummyInfoResults.append({"IDs": [ArticleId]})

    articleTextIds = zip(ReferencePatterns, ArticleIDs)
    for TEXT in articleTextIds:
        print("%s\t%s" % (TEXT[0], TEXT[1]))

    print("Expanding References %i/%i" % (len(ArticleInfoResults),
                                          len(ArticleIDs)))

    ManuscriptText = renderCitationInManuscript(ManuscriptText,
                                                ReferencePatterns,
                                                ArticleIDs,
                                                projectDefinitions)

    for A in ArticleInfoResults:
        assert isinstance(A, str)

    return ManuscriptText, ArticleInfoResults, notFound


def renderCitationInManuscript(ManuscriptText: str,
                               ReferencePatterns: List[str],
                               BibIDs: List[str],
                               projectDefinitions) -> str:

    CitationCommands = loadCitationCommands(projectDefinitions)

    notFound = []
    for o, ocurrence in enumerate(ReferencePatterns):
        Found = False
        for BibID in BibIDs:
            if BibIDs[o] in BibID:
                if "<" in ocurrence:
                    TexCommand = '\\%s' % CitationCommands[1]
                elif "V" in ocurrence:
                    TexCommand = '\\%s' % CitationCommands[2]
                else:
                    TexCommand = '\\%s' % CitationCommands[0]

                TexCommand += "{%s}"

                Replacement = TexCommand % BibID[0]
                ManuscriptText = ManuscriptText.replace(
                    ocurrence,
                    Replacement, 1)

                Found = True
                break

        if not Found:
            notFound.append(BibIDs[o])
            print("NOT FOUND %s" % BibIDs[o])

    return ManuscriptText
