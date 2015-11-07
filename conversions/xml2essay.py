from pynlpl.formats import folia

O = folia.CorrectionHandling.ORIGINAL


doc = folia.Document(file='../data/out.xml')
for sentence in doc.sentences():
    print sentence
    if sentence.hasannotationlayer(folia.SemanticRolesLayer):
        layer = sentence.layers(folia.SemanticRolesLayer)[0]
        for annotation in layer.annotations(folia.SemanticRole):
            for word in annotation.select(folia.Word):
                print word,
            print annotation.cls

    if sentence.corrections(): 
        for correction in sentence.select(folia.Correction):
            o = correction.text(correctionhandling=O) if correction.hastext(correctionhandling=O) else ''
            n = correction.text() if correction.hastext() else ''
            #o = str(correction.original()) if correction.original().hastext() else ''
            #n = str(correction.new()) if correction.new().hastext() else ''
            print 'CORRECTIE: ' + o + '/' + n
