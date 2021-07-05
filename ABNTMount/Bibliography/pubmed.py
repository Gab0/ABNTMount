#!/bin/python

"""

Fetch article information from PUBMED.

"""

import sys
import os
import copy
import json
import pandas as pd
from Bio import Entrez

from ..Output import renderBib
Entrez.email = "ABNTMount"


def getCitationInfo(query):
    W = Entrez.esearch(db='pubmed', term=query, retmax=1666)
    A = Entrez.read(W)
    IdList = A['IdList']
    if A['Count'] != '1':
        print(A)
        sys.exit("Search for article named as %s failed!" % query)

    W = Entrez.efetch(db='pubmed', id=IdList, rettype='xml')
    W = Entrez.read(W)

    W = W['PubmedArticle'][0]
    Authors = W['MedlineCitation']['Article']['AuthorList']
    # Authors = ["%s, %s" % (x['LastName'], x['Initials']) for x in Authors]
    # Authors = '; '.join(Authors)
    print(W['MedlineCitation']['Article'])
    sys.exit()
    INFO = {
        "Authors": Authors,
        'Year': W['PubmedData']['History'][0]['Year'],
        'Journal': W['MedlineCitation']['Article']['Journal']['Title'],
        'Title': W['MedlineCitation']['Article']['ArticleTitle'],
    }

    return INFO


# FIXME: DEPRECATED?
# The use of preloaded bib files seems a better alternative.
def loadPreloadedArticleInfo(preloadedArticleInfoPath, queries):

    preloaded = []
    current_preloaded = []

    if not os.path.isfile(preloadedArticleInfoPath):
        return [], []
    preloadedAI = pd.read_csv(preloadedArticleInfoPath)

    def buildAuthors(authorString):
        a = authorString.split(",")
        a = [w.strip() for w in a]
        a = [{
            "CollectiveName": w
        } for w in a]

        return a

    preloaded_ids = list(preloadedAI.ID)
    print(preloaded_ids)
    for q in queries:
        if q in preloaded_ids:
            ID = q
            info = preloadedAI[preloadedAI.ID == ID].iloc[0]
            article = {
                "IDs": [ID],
                "Authors": buildAuthors(info.Authors),
                "Year": info.Year,
                "Title": info.Title,
                "Journal": info.Journal,

            }
            preloaded.append(article)
            print(article)
            print("PRELOADED!!!")
            print(q)
            print(preloadedAI)
            current_preloaded.append(ID)

    return preloaded, current_preloaded


def has_digit(v):
    return any([d for d in v if d.isdigit()])


def getBatchCitationInfo(WorkingDirectory, queries, Verbose=False):

    # read article info from preloaded article info file.
    preloadedArticleInfoPath = os.path.join(WorkingDirectory,
                                            "preloadedArticleInfo.csv")

    preloaded, current_preloaded = loadPreloadedArticleInfo(
        preloadedArticleInfoPath, queries)

    # remote PUBMED metadata retriever;
    # prepare search query;
    filtered_queries = [
        q for q in queries
        if q not in current_preloaded and has_digit(q)
    ]

    for q, query in enumerate(filtered_queries):
        if query.isdigit():
            filtered_queries[q] += '[uid]'

    searchTerm = ' OR '.join(filtered_queries)

    if Verbose:
        print(searchTerm)

    if not filtered_queries:
        return preloaded

    IdQuery = Entrez.esearch(db='pubmed', term=searchTerm, retmax=3666)
    IdQuery = Entrez.read(IdQuery)
    IdList = IdQuery['IdList']
    if Verbose:
        print("IdList of %i" % len(IdList))

    W = Entrez.efetch(db='pubmed', id=IdList, rettype='xml')
    W = Entrez.read(W)

    return list(map(parseArticle, W['PubmedArticle'])) + preloaded


def parseArticle(Article):
    def getVolume(Article):
        Data = Article['MedlineCitation']['Article']['Journal']['JournalIssue']
        if "Volume" in Data.keys():
            return Data["Volume"]
        if "Issue" in Data.keys():
            return Data["Issue"]
        return ""

    Authors = Article['MedlineCitation']['Article']['AuthorList']
    # Authors = ["%s, %s" % (x['LastName'], x['Initials']) for x in Authors]
    # Authors = '; '.join(Authors)
    BackwardIDs = Article['PubmedData']['ArticleIdList']
    BackwardIDs = [str(x) for x in BackwardIDs]

    Title = Article['MedlineCitation']['Article']['ArticleTitle']
    Title = Title.replace('<i>', '\\textit{').replace('</i>', '}')

    try:
        INFO = {
            "IDs": BackwardIDs,
            "Authors": Authors,
            'Year': Article['PubmedData']['History'][0]['Year'],
            'Journal':
            Article['MedlineCitation']['Article']['Journal']['Title'],
            'JournalInfo': {
                'Volume': getVolume(Article)
            },
            'Title': Title,
        }

    except KeyError as e:
        print(e)
        print(json.dumps(
            Article['MedlineCitation']['Article'], indent=4))
        print("ERROR!")
        sys.exit()

    return BackwardIDs, renderBib.makeBibEntry(INFO)
