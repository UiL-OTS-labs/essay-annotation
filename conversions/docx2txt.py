import codecs

from docx import Document

document = Document('../data/test_errors.docx')
for table in document.tables:
    filename = table.rows[0].cells[0].text.split(' ')[0]
    with codecs.open('../data/' + filename + '.txt', 'wb') as f:
        for i, row in enumerate(table.rows):
            for j, cell in enumerate(row.cells):
                if i != 0 and j == 0:
                    f.write(cell.text.replace('\n', ' ').encode('utf8'))
                    f.write('\n')
