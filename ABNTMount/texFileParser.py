#!/bin/python

def parseTexFile(texFilePath,
                 PretextualSequence,
                 ManuscriptSequence,
                 ManuscriptParts):

    texFile = open(texFilePath).read()
    pretextualReplacementToken = "%[[PRETEXTUAL-CONTENT]]"
    chapterReplacementToken = "%[[CHAPTER-CONTENT]]"


    pretextualLines = []
    if pretextualReplacementToken in texFile:
        for p, Pretextual in enumerate(PretextualSequence):
            pretextualdef = "\input{%s}" % Pretextual
            pretextualLines.append(pretextualdef)


    texFile = texFile.replace(pretextualReplacementToken,
                              "\n".join(pretextualLines))
    chapterLines = []
    if chapterReplacementToken in texFile:
        for m, Manuscript in enumerate(ManuscriptSequence):
            for PartIndex, PartName in ManuscriptParts:
                if PartIndex == m:
                    partdef = "\part{%s}" % PartName
                    chapterLines.append(partdef)
                    break

            Line = "\input{%s}" % Manuscript
            chapterLines.append(Line)

    texFile = texFile.replace(chapterReplacementToken,
                              "\n".join(chapterLines))

    return texFile

