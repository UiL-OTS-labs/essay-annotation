# essay-annotation
Parses essay annotation into FoLiA XML

This project contains scripts to convert Word documents with a specific markup (called essay annotation) to [FoLiA XML](https://proycon.github.io/folia/).
After the conversion is complete, there are scripts available to output the results to .csv- or .html-format.
You can find details on the scripts below.

## Preprocessing

### Word to plain text

Call `conversions/docx2txt.py` with the specified file to convert the document to plain text files.

### Plain text to FoLiA

Call `conversions/essay2xml.py` to convert the plain-text files to FoLiA.

## Conversions

### FoLiA to HTML

Call `conversions/folia2html.py` to convert the plain-text files to FoLiA.

### FoLiA to .csv

Call `conversions/xml2csv.py` to convert the plain-text files to FoLiA.

### FoLiA to .txt

Call `conversions/xml2txt.py` to convert the plain-text files to FoLiA.

