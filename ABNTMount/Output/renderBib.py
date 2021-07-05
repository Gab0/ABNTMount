import os


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
        'journal = "%s",' % ArticleInfo['Journal'].replace('&', "\\&"),
        # 'number = "%s",' % ArticleInfo,
        # 'pages = "%s"' % ArticleInfo,
    ]

    try:
        entry.append('volume = "%s",' % ArticleInfo['JournalInfo']['Volume'])
    except Exception as E:
        print(f"Failure to find journal info. {E}")

    entry.append("}")

    return '\n'.join(entry)


def renderBibtexFile(BIBFilePath,
                     BaseBIBFilePath,
                     ManuscriptDirectory,
                     ArticleContents):

    # -- BUILD BIBTEX CITAITON INFO;
    BIBFile = '\n\n'.join(ArticleContents)

    # -- parse base bib info;
    if BaseBIBFilePath is not None:
        if os.path.isfile(BaseBIBFilePath):
            BaseBIBFile = open(BaseBIBFilePath).read() + "\n\n"
            BIBFile = BaseBIBFile + BIBFile

    with open(BIBFilePath, 'w') as f:
        f.write(BIBFile)
