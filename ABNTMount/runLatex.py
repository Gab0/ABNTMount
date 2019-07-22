#!/bin/python

import os
import subprocess


def runLatex(options, TexPath, WD):
    TexPathBody = TexPath.split('.')[0]

    # Define Commands;
    LatexCMD = ['xelatex', TexPath]
    BIBCMD = ['bibtex', TexPathBody]
    docCMD = ['mk4ht', 'ooxelatex', TexPath]
    # pandocCMD = ["pandoc", "-s", TexPath, "-o", "%s.txt" % TexPath]
    ENV = os.environ.copy()
    ENV["openout_any"] = "a"

    if options.linkReferences:
        commandSequence = [
            LatexCMD,
            BIBCMD,
            LatexCMD,
            LatexCMD,
            LatexCMD,
            LatexCMD
            ]
    else:
        commandSequence = [LatexCMD, LatexCMD]
    if False:
        commandSequence.append(docCMD)
    for CMD in commandSequence:
        W = subprocess.Popen(CMD, cwd=WD, env=ENV)
        success = W.wait()
        if options.debugMode:
            print("%s\n%i" % (" ".join(CMD), success))
            input("Debug: Press enter to continue.")


def makeBibEntry(ArticleInfo):
    def parseAuthors(Authors):
        _Authors = []
        for Author in Authors:
            try:
                if 'ForeName' in Author.keys():
                    A = ' '.join([Author['ForeName'], Author['LastName']])
                elif 'LastName' in Author.keys():
                    A = Author['LastName']
                else:
                    A = Author['CollectiveName']
            except Exception as e:
                print(Author)
                print(e)
            _Authors.append(A)
        return ' and '.join(_Authors)

    def parseTitle(Title):
        Quote = '\"'
        if Quote in Title:
            Title = Title.replace(Quote, "``", 1)
            Title = Title.replace(Quote, "''", 1)
        return Title

    entry = [
        "@article{%s," % ArticleInfo['IDs'][0],
        'author = "%s",' % parseAuthors(ArticleInfo['Authors']),
        'title = "%s",' % parseTitle(ArticleInfo['Title']),
        'year = "%s",' % ArticleInfo['Year'],
        'journal = "%s",' % ArticleInfo['Journal'].replace('&', "\&"),
        #'number = "%s",' % ArticleInfo,
        #'pages = "%s"' % ArticleInfo,
    ]
    try:
        entry.append('volume = "%s",' % ArticleInfo['JournalInfo']['Volume'])
    except Exception as E:
        print("Failure to find journal info.")

    entry.append("}")

    return '\n'.join(entry)
