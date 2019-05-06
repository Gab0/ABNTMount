#!/bin/python

from textFormat import C, Nt, Bt
from odf.text import P, Span

def makeFrontFace(info):
    FrontPage = []
    SecondPage = []

    INTERSPACE = lambda x: [P() for z in range(x)]

    INSTITUTION = lambda: C(Bt(info['institution'].upper()))
    AUTHOR = lambda: C(Nt(info['author'].upper()))
    TITLE = lambda: C(Nt(info['title'].upper()))
    SUBTITLE = lambda: C(Nt(info['subtitle']))
    CITY = lambda: C(Nt("%s - %s" % (info['city'], info['state'])))
    YEAR = lambda: C(Nt(info['date-short'].split('/')[-1]))
    BE = C(Nt('BANCA EXAMINADORA'))
    DECLARATION = C(Nt('Relatório final apresentado à\nUniversidade %s como parte das\n exigências para a obtenção do título de\n%s' %\
                       (info['institution-short'], 'Bacharel em Biologia')), style='right')
    HORIZONTALBAR = lambda: C(Nt("_" * 40))
    PROFSIGNATURE = lambda name: [HORIZONTALBAR(), C(Nt("Prof. %s" % name))]

    FrontPage = [
        INSTITUTION(), *INTERSPACE(3),
        AUTHOR(), *INTERSPACE(18),
        TITLE(),
        SUBTITLE(), *INTERSPACE(19),
        CITY(),
        YEAR()
    ]

    SecondPage = [
        AUTHOR(), *INTERSPACE(3),
        TITLE(),
        SUBTITLE(), *INTERSPACE(3), DECLARATION, *INTERSPACE(3), BE,
        *INTERSPACE(4), *PROFSIGNATURE(''), *INTERSPACE(4), *PROFSIGNATURE(''),
        *INTERSPACE(4), *PROFSIGNATURE(''),
        P(stylename='Pagebreak')
    ]
    return FrontPage + SecondPage
