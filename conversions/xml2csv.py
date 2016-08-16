import glob
import os
import re
from string import punctuation

from pynlpl.formats import folia

from utils import UnicodeWriter

REMOVE_SPACES = re.compile(r'\s+([{}])+'.format(re.escape(punctuation)))


def get_feature(element, subset):
    """
    Retrieve a Feature for an element (Correction/SemanticRole) given a subset.
    """
    features = []
    for feature in element.select(folia.Feature, recursive=False):
        if feature.subset == subset:
            features.append(feature)

    result = ''
    if len(features) == 1:
        result = features[0].cls
    elif len(features) > 1:
        raise ValueError('Multiple features for ' + element.cls)
    return result


def get_corrections(element, doc_id, sentence_nr):
    """
    Retrieves all Corrections for an element.
    As Correction can have multiple Originals, use this as the base and return one line per Original.
    """
    result = []
    for c in element.select(folia.Correction, recursive=False):
        for original in c.select(folia.Original, ignore=False):
            correction = original.ancestor()
            problem = get_feature(correction, 'problem')
            pos = get_feature(correction, 'pos')
            original = remove_spaces(correction.text(correctionhandling=folia.CorrectionHandling.ORIGINAL))
            corrected = remove_spaces(correction.text(correctionhandling=folia.CorrectionHandling.CURRENT))
            s_original = c.ancestor(folia.Sentence).text(correctionhandling=folia.CorrectionHandling.ORIGINAL)
            s_corrected = c.ancestor(folia.Sentence).text(correctionhandling=folia.CorrectionHandling.CURRENT)
            result.append([doc_id, sentence_nr, original, corrected, correction.cls, problem, pos, s_original, s_corrected])
    return result


def get_text_from_semrole(semrole):
    try:
        return remove_spaces(semrole.text())
    except folia.NoSuchText:
        return ''


def remove_spaces(s):
    """
    Removes all spaces before punctuation.
    TODO: probably better if we regulate this in the XML output ('nospace' attribute).
    """
    return REMOVE_SPACES.sub(r'\1', s)


def process_file(csv_writer, filename):
    """
    Reads a single FoLiA .xml-file, loops over its Sentences,
    and writes the annotations (Correction/SemanticRole) to the csv file.
    """
    doc = folia.Document(file=filename)

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
            try:
                s_original = sentence.text(correctionhandling=folia.CorrectionHandling.ORIGINAL)
                s_corrected = sentence.text(correctionhandling=folia.CorrectionHandling.CURRENT)
            except folia.NoSuchText:
                s_original = ''
                s_corrected = ''
            csv_writer.writerow([doc.id, sentence_nr, get_text_from_semrole(semrole), '', semrole.cls, problem, pos, s_original, s_corrected])


def process_folder(folder):
    """
    Writes annotations from all FoLiA .xml-files from the given folder to a .csv-file.
    """
    # Create an output .csv-file
    with open(os.path.join(folder, 'annotations.csv'), 'wb') as csv_file:
        csv_file.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
        csv_writer = UnicodeWriter(csv_file, delimiter=';')
        csv_writer.writerow(['tekstnummer', 'zin nr',
                             'geannoteerde passage', 'correctie',
                             'eenheid', 'probleem', 'woordsoort',
                             'originele zin', 'gecorrigeerde zin'])

        # Loop over all .xml-files in the given folder
        for filename in glob.glob(os.path.join(folder, '*.xml')):
            print 'Processing ', filename
            process_file(csv_writer, filename)

if __name__ == '__main__':
    process_folder('../data/out')
