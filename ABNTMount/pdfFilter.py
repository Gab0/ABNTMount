#!/bin/python

from PyPDF2 import PdfFileWriter, PdfFileReader


def fromPageContains(filepath, outfilepath, keyword):
    infile = PdfFileReader(filepath, 'rb')
    output = PdfFileWriter()

    Found = False
    for i in range(infile.getNumPages()):
        Page = infile.getPage(i)
        Text = Page.extractText()
        if keyword in Text:
            Found = True
            break

    if Found:
        print("keyword found on text. proceeding to trim it")
    else:
        print("keyword not found on text. rewriting it!")

    Keep = False
    for i in range(infile.getNumPages()):
        Page = infile.getPage(i)
        Text = Page.extractText()
        if Found:
            if keyword in Text:
                Keep = True
            if Keep:
                output.addPage(Page)
        else:
            output.addPage(Page)

    with open(outfilepath, 'wb') as f:
        output.write(f)
