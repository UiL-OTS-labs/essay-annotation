from pynlpl.formats import folia

doc = folia.Document(file='data/out.xml')
for sentence in doc.sentences():
    print sentence