#!/bin/python

import csv
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.text import P, Span, SoftPageBreak


def parseTableFromCsv(tablePath, tableInfo):
    F = open(tablePath, 'r')
    TableData = csv.reader(F)

    table = Table(name=tableInfo['name'], stylename='')
    getColumn = True
    for row in TableData:
        tr = TableRow()
        for value in row:
            if getColumn:
                table.addElement(TableColumn())
            p = P(text=value)
            cell = TableCell(valuetype="string")
            cell.addElement(p)
            tr.addElement(cell)
        getColumn = False
        table.addElement(tr)

    return table


def applyLayoutToTable(table):
    print(table)
