import codecs
import os
import re

from pynlpl.formats import folia

from models import PartAnnotation

CORRECTIONS_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/config/corrections.foliaset.xml'
SEMANTICROLES_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/config/semanticroles.foliaset.xml'

HAS_INNER = re.compile(r'\[[^\]]*\[')
GREEDY_MATCH_TAG = re.compile(r'\[(.*)\](\w[\*\w]*)')
LAZY_MATCH_TAG = re.compile(r'\[(.*?)\](\w[\*\w]*)')


def match_outer(s, pa=None):
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
    matches = LAZY_MATCH_TAG.finditer(s)
    if not pa:
        pa = PartAnnotation(s, None)
    for match in matches:
        # If we match the whole sentence, create a new annotation
        if match.group(0) == s:
            sentence = match.group(1)
            annotation = match.group(2)
            pa = PartAnnotation(sentence, annotation)
        # Otherwise, add the matches to the existing annotation
        else:
            pa.add_child(PartAnnotation(match.group(1), match.group(2)), match.start(0), match.end(0))
    return pa


def extract_corrections(s, pa=None):
    if has_inner(s):
        if pa is not None:
            pa = match_outer(s, pa)
        else:
            pa = match_outer(s)
    else:
        pa = match_inner(s, pa)
    return pa


def has_inner(s): 
    return HAS_INNER.search(s)


def count_brackets(line):
    return line.count('[') == line.count(']')


def start_folia_document(filename):
    doc = folia.Document(id=filename)
    doc.declare(folia.Correction, CORRECTIONS_SET)
    doc.declare(folia.SemanticRolesLayer, SEMANTICROLES_SET)
    text = doc.append(folia.Text)
    paragraph = text.add(folia.Paragraph)
    return doc


def process_line(line, doc):
    line = line.strip()
    pa = extract_corrections(line)
    sentence = doc.paragraphs().next().add(folia.Sentence)
    _, roles = pa.to_folia_sentence(doc, sentence)
    if roles:
        layer = sentence.add(folia.SemanticRolesLayer)
        for role in roles:
            layer.add(role)


def process_file(filename):
    with codecs.open(filename, 'rb') as f:
        doc = start_folia_document(os.path.splitext(os.path.basename(filename))[0])
        for n, line in enumerate(f):
            if count_brackets(line):
                process_line(line, doc)
            else:
                print 'Number of brackets does not match on line', n
        doc.save('../data/out.xml')


if __name__ == '__main__':
    process_file('../data/T1_VOWY0Q147044.txt')
