from pynlpl.formats import folia

from utils import UnicodeWriter


def get_feature(element, subset):
    features = []
    for feature in element.select(folia.Feature, recursive=False):
        if feature.subset == subset:
            features.append(feature)

    result = ''
    if len(features) == 1:
        result = features[0].cls
    elif len(features) > 1:
        print 'Multiple features for ' + element.cls
    return result

doc = folia.Document(file='../data/out/T1_VOWYQ147140.xml')

with open('../data/out/comments.csv', 'wb') as csv_file:
    csv_file.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
    csv_writer = UnicodeWriter(csv_file, delimiter=';')
    header = ['tekstnummer', 'zin nr', 'geannoteerde passage', 'correctie', 'eenheid', 'probleem', 'woordsoort']
    csv_writer.writerow(header)

    for sentence in doc.sentences():
        sentence_nr = sentence.id.split('.')[-1]
        for correction in sentence.select(folia.Correction, recursive=False):
            problem = get_feature(correction, 'problem')
            pos = get_feature(correction, 'pos')
            original = correction.text(correctionhandling=folia.CorrectionHandling.ORIGINAL)
            corrected = correction.text(correctionhandling=folia.CorrectionHandling.CURRENT)
            csv_writer.writerow([doc.id, sentence_nr, original, corrected, correction.cls, problem, pos])
        for word in sentence.words():
            for correction in word.select(folia.Correction, recursive=False):
                problem = get_feature(correction, 'problem')
                pos = get_feature(correction, 'pos')
                original = correction.text(correctionhandling=folia.CorrectionHandling.ORIGINAL)
                corrected = correction.text(correctionhandling=folia.CorrectionHandling.CURRENT)
                csv_writer.writerow([doc.id, sentence_nr, original, corrected, correction.cls, problem, pos])
        for semrole in sentence.select(folia.SemanticRole):
            problem = get_feature(semrole, 'problem')
            pos = get_feature(semrole, 'pos')
            csv_writer.writerow([doc.id, sentence_nr, semrole.text(), '-', semrole.cls, problem, pos])
