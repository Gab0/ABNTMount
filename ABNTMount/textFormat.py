#!/bin/python
from odf.text import P, Span


def Bt(content):
    return Span(text=content, stylename='boldtext')


def Nt(content):
    return Span(text=content, stylename='plaintext')


def C(content, style='centerized'):
    Q = P(stylename=style)
    Q.addElement(content)
    return Q
