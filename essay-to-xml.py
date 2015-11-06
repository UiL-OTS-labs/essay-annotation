import codecs
import re

from pynlpl.formats import folia

from models import PartAnnotation

HAS_INNER = re.compile(r'\[[^\]]*\[')
GREEDY_MATCH_TAG = re.compile(r'\[(.*)\](\w[\*\w]*)')
NON_GREEDY_MATCH_TAG = re.compile(r'\[(.*?)\](\w[\*\w]*)')


def match_outer(s, pa=None):
    # TODO: this does not work:
    # [Zwarte pieten/Zwarte Pieten]HN*O zijn zwart als [roed/roet]SPE*I*N [/.]L*O
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
    matches = NON_GREEDY_MATCH_TAG.finditer(s)
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
    if HAS_INNER.search(s):
        if pa is not None:
            pa = match_outer(s, pa)
        else:
            pa = match_outer(s)
    else:
        pa = match_inner(s, pa)
    return pa


def count_brackets(line):
    return line.count('[') == line.count(']')


def process_file():
    doc = folia.Document(id='example')
    doc.declare(folia.Correction, 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/config/corrections.foliaset.xml')
    doc.declare(folia.SemanticRolesLayer, 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/config/semanticroles.foliaset.xml')
    text = doc.append(folia.Text)
    paragraph = text.add(folia.Paragraph)
    with codecs.open('data/T1_VOWY0Q147044.txt', 'rb') as f:
        for n, line in enumerate(f):
            line = line.strip()
            if count_brackets(line):
                pa = extract_corrections(line)
                sentence = paragraph.add(folia.Sentence)
                roles = pa.to_folia_sentence(doc, sentence)
                if roles:
                    layer = sentence.add(folia.SemanticRolesLayer)
                    for role in roles:
                        layer.add(role)
            else:
                print 'Number of brackets does not match on line', n
    doc.save('data/out.xml')


if __name__ == '__main__':
    process_file()
