#!/bin/python

import sys
import os
import subprocess


def runLatex(options, TexPath, WD):
    TexPathBody = TexPath.split('.')[0]

    # Define Commands;
    LatexCMD = [options.LatexExecutable, "-halt-on-error", TexPath]
    BIBCMD = ['bibtex', TexPathBody]
    docCMD = ['mk4ht', 'ooxelatex', TexPath]
    # pandocCMD = ["pandoc", "-s", TexPath, "-o", "%s.txt" % TexPath]
    ENV = os.environ.copy()
    ENV["openout_any"] = "a"

    if options.linkReferences:
        commandSequence = [
            LatexCMD,
            BIBCMD
        ] + [LatexCMD] * 4

    else:
        commandSequence = [LatexCMD, LatexCMD]
    if False:
        commandSequence.append(docCMD)

    results = []
    for CMD in commandSequence:
        W = subprocess.Popen(CMD, cwd=WD, env=ENV)
        success = W.wait()
        results.append(success)
        if options.debugMode:
            print("%s\n%i" % (" ".join(CMD), success))
            input("Debug: Press enter to continue.")

    if any(r == 1 for r in results):
        print("ABNTMount failure: LATEX ERROR.")
        for cmd, res in zip(commandSequence, results):
            cmd = " ".join(cmd)
            print(f"{cmd} - {res}")
        print(results)
        sys.exit(1)

