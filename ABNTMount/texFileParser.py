#!/bin/python


def parseTexFile(texFilePath,
                 segmentSequences,
                 replacementTokens,
                 ManuscriptParts):

    texFile = open(texFilePath).read()

    for s, segmentSequence in enumerate(segmentSequences):
        replacementToken = replacementTokens[s]
        segmentLines = []
        if replacementToken in texFile:
            for m, SegmentFilepath in enumerate(segmentSequence):
                if ManuscriptParts[s]:
                    for PartIndex, PartName in ManuscriptParts[s]:
                        if PartIndex == m:
                            partdef = "\part{%s}" % PartName
                            segmentLines.append(partdef)
                            break
                segmentBlock = "\input{%s}" % SegmentFilepath
                segmentLines.append(segmentBlock)
                segmentLines.append("\clearpage")
        texFile = texFile.replace(replacementToken,
                                  "\n".join(segmentLines))

    return texFile
