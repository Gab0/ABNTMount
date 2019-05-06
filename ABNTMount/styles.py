#!/bin/python

from odf.style import Style, TextProperties, ParagraphProperties


def createStyles(Handler, StyleData):
    for W in StyleData['text'].keys():
        style = Style(name=W, family="text")
        props = TextProperties(attributes=StyleData['text'][W])
        style.addElement(props)
        Handler.addElement(style)
    for W in StyleData['paragraph'].keys():
        paragraph = Style(name=W, family="paragraph")
        props = ParagraphProperties(attributes=StyleData['paragraph'][W])
        paragraph.addElement(props)
        Handler.addElement(paragraph)

    pagebreak = Style(name="Pagebreak", family="paragraph")
    _break = ParagraphProperties(breakafter="page")
    pagebreak.addElement(_break)
    Handler.addElement(pagebreak)


def setupABNT(textstyles):
    createStyles(
        textstyles, {
            'text': {
                'boldtext': {
                    'fontsize': "12pt",
                    'fontweight': "bold",
                    'fontfamily': 'Arial'
                },
                'plaintext': {
                    'fontsize': "12pt",
                    'fontfamily': 'Arial'
                }
            },
            'paragraph': {
                'Global': {
                    "linespacing": "6.66pt"
                },
                'centerized': {
                    "linespacing": "6.66pt",
                    "textalign": "center"
                },
                'right': {
                    "linespacing": "6.66pt",
                    "textalign": "right"
                }
            }
        })
