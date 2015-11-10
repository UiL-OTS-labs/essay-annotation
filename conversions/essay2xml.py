import codecs
import os
import re

from pynlpl.formats import folia

from models import PartAnnotation

CORRECTIONS_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/master/config/corrections.foliaset.xml'
SEMANTICROLES_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/master/config/semanticroles.foliaset.xml'

HAS_INNER = re.compile(r'\[[^\]]*\[')
GREEDY_MATCH_TAG = re.compile(r'\[(.*)\](\w[\*\w]*)')
LAZY_MATCH_TAG = re.compile(r'\[(.*?)\](\w[\*\w]*)')


def match_outer(s, pa=None):
    """
    Matches the outer annotation (greedy) in a nested annotation.
    """
    match = GREEDY_MATCH_TAG.search(s)
    if match:
        sentence = match.group(1)
        annotation = match.group(2)
        if not pa:
            pa = PartAnnotation(sentence, annotation)
        else:
            p_child = PartAnnotation(sentence, annotation)
            pa.add_child(p_child, match.start(0), match.end(0))
            pa = p_child
        extract_corrections(sentence, pa)
    else:
        print 'not found?'
    return pa


def match_inner(s, pa=None):
    """
    Matches all inner annotations (lazy) in a non-nested annotation.
    """
    if not pa:
        pa = PartAnnotation(s, None)

    matches = LAZY_MATCH_TAG.finditer(s)
    for match in matches:
        sentence = match.group(1)
        annotation = match.group(2)
        # If we match the whole sentence, create a new annotation
        if match.group(0) == s:
            pa = PartAnnotation(sentence, annotation)
        # Otherwise, add the matches to the existing annotation
        else:
            pa.add_child(PartAnnotation(sentence, annotation), match.start(0), match.end(0))
    return pa


def extract_corrections(s, pa=None):
    if is_nested(s):
        pa = match_outer(s, pa)
    else:
        pa = match_inner(s, pa)
    return pa


def is_nested(s):
    """
    Checks whether the string s has a nested structure.
    """
    return HAS_INNER.search(s)


def count_brackets(line):
    """
    Matches the number of brackets on a line.
    """
    return line.count('[') == line.count(']')


def start_folia_document(filename):
    """
    Creates a FoLiA document, declares the annotation types and adds a Text and Paragraph.
    TODO: set correct metadata.
    """
    doc = folia.Document(id=filename)
    doc.declare(folia.Correction, CORRECTIONS_SET, annotatortype=folia.AnnotatorType.MANUAL)
    doc.declare(folia.SemanticRole, SEMANTICROLES_SET, annotatortype=folia.AnnotatorType.MANUAL)
    doc.metadata = folia.NativeMetaData(score='88', time='3', words='110')  # TODO: set this correctly
    text = doc.append(folia.Text)
    text.add(folia.Paragraph)
    return doc


def process_line(line, doc):
    """
    Processes a single line from the plain-text annotation and converts that to a FoLiA Sentence.
    """
    # Create a new sentence in the document
    sentence = doc.paragraphs().next().add(folia.Sentence)

    # Strip the line and create a PartAnnotation structure
    line = line.strip()
    pa = extract_corrections(line)

    # Convert the PartAnnotation structure to a FoLiA Sentence
    _, roles = pa.to_folia_sentence(doc, sentence)

    # Add all collected roles to the SemanticRolesLayer
    if roles:
        layer = sentence.add(folia.SemanticRolesLayer)
        for role in roles:
            layer.add(role)


def process_file(filename):
    """
    Processes a plain-text annotation file and converts that to FoLiA XML.
    """
    with codecs.open(filename, 'rb') as f:
        doc = start_folia_document(os.path.splitext(os.path.basename(filename))[0])
        for n, line in enumerate(f):
            if count_brackets(line):
                process_line(line, doc)
            else:
                print 'Number of brackets does not match on line', n
        doc.save('../data/out.xml')


if __name__ == '__main__':
    process_file('../data/T1_VOWYQ147140.txt')
