#!/bin/python

import os
import pandas as pd
from Bio import Entrez
import copy
Entrez.email = "ABNTMount"


def getCitationInfo(query):
    W = Entrez.esearch(db='pubmed', term=query, retmax=1666)
    A = Entrez.read(W)
    IdList = A['IdList']
    if A['Count'] != '1':
        print(A)
        exit("Search for article named as %s failed!" % query)

    W = Entrez.efetch(db='pubmed', id=IdList, rettype='xml')
    W = Entrez.read(W)

    W = W['PubmedArticle'][0]
    Authors = W['MedlineCitation']['Article']['AuthorList']
    # Authors = ["%s, %s" % (x['LastName'], x['Initials']) for x in Authors]
    # Authors = '; '.join(Authors)
    print(W['MedlineCitation']['Article'])
    exit()
    INFO = {
        "Authors": Authors,
        'Year': W['PubmedData']['History'][0]['Year'],
        'Journal': W['MedlineCitation']['Article']['Journal']['Title'],
        'Title': W['MedlineCitation']['Article']['ArticleTitle'],
    }

    return INFO


def getBatchCitationInfo(queries, Verbose=False):
    queries = copy.deepcopy(queries)

    # read article info from preloaded article info file.
    preloadedArticleInfoPath = "preloadedArticleInfo.csv"
    if os.path.isfile(preloadedArticleInfoPath):
        preloaded = []
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
        current_preloaded = []
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

    # remote PUBMED metadata retriever;
    # prepare search query;
    queries = [q for q in queries if q not in current_preloaded]
    for q in range(len(queries)):
        if queries[q].isdigit():
            queries[q] += '[uid]'

    searchTerm = ' OR '.join(queries)

    if Verbose:
        print(searchTerm)

    if queries:
        IdQuery = Entrez.esearch(db='pubmed', term=searchTerm, retmax=1666)
        IdQuery = Entrez.read(IdQuery)
        IdList = IdQuery['IdList']
        if Verbose:
            print("IdList of %i" % len(IdList))

        W = Entrez.efetch(db='pubmed', id=IdList, rettype='xml')
        W = Entrez.read(W)

        CitationInfo = []
        for A, Article in enumerate(W['PubmedArticle']):
            Authors = Article['MedlineCitation']['Article']['AuthorList']
            # Authors = ["%s, %s" % (x['LastName'], x['Initials']) for x in Authors]
            # Authors = '; '.join(Authors)
            BackwardIDs = Article['PubmedData']['ArticleIdList']
            BackwardIDs = [str(x) for x in BackwardIDs]

            Title = Article['MedlineCitation']['Article']['ArticleTitle']
            Title = Title.replace('<i>', '\\textit{').replace('</i>', '}')
            INFO = {
                "IDs": BackwardIDs,
                "Authors": Authors,
                'Year': Article['PubmedData']['History'][0]['Year'],
                'Journal':
                Article['MedlineCitation']['Article']['Journal']['Title'],
                'JournalInfo': {
                    'Volume': Article['MedlineCitation']['Article']['Journal']['JournalIssue']['Volume']
                },
                'Title': Title,
            }

            CitationInfo.append(INFO)
    else:
        CitationInfo = []

    return CitationInfo + preloaded
