import argparse
import codecs
import os

from docx import Document


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Converts .docx-documents to individual .txt-files.')
    parser.add_argument('filenames', type=str, nargs='+', help='The .docx-files to be processed')
    args = parser.parse_args()
    for f in args.filenames:
        document = Document(f)
        for table in document.tables:
            filename = table.rows[0].cells[0].text.strip().split(' ')[0]
            with codecs.open(os.path.join(os.path.dirname(__file__), '..', 'data', filename + '.txt'), 'wb') as f:
                for i, row in enumerate(table.rows):
                    for j, cell in enumerate(row.cells):
                        if i != 0 and j == 0:
                            f.write((cell.text.replace('\n', ' ') + '\n').encode('utf8'))
