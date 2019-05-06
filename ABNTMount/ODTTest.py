#!/bin/python

from odf.opendocument import OpenDocumentText
from odf.text import P, Span
from odf.style import Style, TextProperties

textdoc = OpenDocumentText()
textstyles = textdoc.styles
sectiontitle = Style(name="Section Title", family="text")
sectiontitle.addElement(
    TextProperties(attributes={
        'fontsize': "12pt",
        'fontweight': "bold"
    }))
textstyles.addElement(sectiontitle)
p = P()
W = Span(
    stylename="Section Title",
    text=
    "A toxoplasmose é uma doença endêmica ao redor de todo o mundo. Acontece..."
)
p.addElement(W)
textdoc.text.addElement(p)
textdoc.save("TEST", True)
print('ok')
