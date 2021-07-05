# ABNTM

This package helps organizing a large manuscript such as a scientific thesis, 
managing its managing multiple chapters and references.

* Organizes file dependencies for the project such as image and csv files.
* Fetches bibliography info from pubmed and DOI.
* Helps managing projects with  multiple `.tex` files that will be combined with `\input`.

# Installation

Clone this repository and install the Python module with the help of Pipy:

`pip install .`

The setup will install the library, the executable `ABNTM`, along with their dependences.

# Usage

Any folder can be the project's working directory.
It must contain a project file, here we will call it `project.yaml`. 
Here's how it should look like:

```

TBD


```

Then run:

`ABNTM -i project.yaml`

This will build the output file.


This guide is incomplete, but `ABNTM -h` might help.

# References

Inside the `.tex` files, an academic reference can be typed anywhere as:

`[@PMID]` or `[@DOI]`

Inputting the article's real PUBMED ID or the article's `DOI`.
