
import requests
import re


def getCitationInfo(DOI):

    header = {"Accept": "text/bibliography; style=bibtex"}
    url = f"http://dx.doi.org/{DOI}"

    req = requests.get(url, headers=header)

    req.encoding = req.apparent_encoding
    content = req.text.strip()

    BibIDs = re.findall(r"@\w+{([\d\w_-]+),", content)

    try:
        content = content.replace(BibIDs[0], DOI)
    except IndexError:
        print(f"Failure to fetch ID{DOI} ")
        print(content)
        exit(1)
    IDs = [DOI] + BibIDs
    print(IDs)
    return IDs, content
