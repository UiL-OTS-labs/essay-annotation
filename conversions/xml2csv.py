import glob
import os

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


def get_corrections(element, doc_id, sentence_nr):
    result = []
    for correction in element.select(folia.Correction, recursive=False):
        problem = get_feature(correction, 'problem')
        pos = get_feature(correction, 'pos')
        original = correction.text(correctionhandling=folia.CorrectionHandling.ORIGINAL)
        corrected = correction.text(correctionhandling=folia.CorrectionHandling.CURRENT)
        result.append([doc_id, sentence_nr, original, corrected, correction.cls, problem, pos])
    return result


def process(filename):
    doc = folia.Document(file=filename)
    pre, _ = os.path.splitext(filename)
    with open(pre + '.csv', 'wb') as csv_file:
        csv_file.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
        csv_writer = UnicodeWriter(csv_file, delimiter=';')
        header = ['tekstnummer', 'zin nr', 'geannoteerde passage', 'correctie', 'eenheid', 'probleem', 'woordsoort']
        csv_writer.writerow(header)

        for sentence in doc.sentences():
            sentence_nr = sentence.id.split('.')[-1]

            # Add Corrections on Sentence and Word level
            csv_writer.writerows(get_corrections(sentence, doc.id, sentence_nr))
            for word in sentence.words():
                csv_writer.writerows(get_corrections(word, doc.id, sentence_nr))

            # Add SemanticRoles
            for semrole in sentence.select(folia.SemanticRole):
                problem = get_feature(semrole, 'problem')
                pos = get_feature(semrole, 'pos')
                csv_writer.writerow([doc.id, sentence_nr, semrole.text(), '', semrole.cls, problem, pos])

if __name__ == '__main__':
    for filename in glob.glob('../data/out/*.xml'):
        process(filename)
