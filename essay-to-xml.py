import codecs
import re

from pynlpl.formats import folia
from pynlpl.textprocessors import tokenize

HAS_INNER = re.compile(r'\[[^\]]*\[')
GREEDY_MATCH_TAG = re.compile(r'\[(.*)\](\w[\*\w]*)')
NON_GREEDY_MATCH_TAG = re.compile(r'\[(.*?)\](\w[\*\w]*)')


class PartAnnotation():
    def __init__(self, part, annotation):
        self.split_part(part)
        self.split_annotation(annotation)
        self.parent = None
        self.children = []

    def split_part(self, part):
        if '/' in part and '[' not in part:
            parts = part.split('/')
            self.original = parts[0]
            self.edited = parts[1]
        else:
            self.original = part
            self.edited = part

    def split_annotation(self, annotation):
        if annotation:
            a = annotation.split('*')
            self.annotation = annotation
            self.unit = a[0]
            self.problem = a[1] if len(a) >= 2 else None
            self.pos = a[2] if len(a) == 3 else None
        else:
            self.annotation = ''
            self.unit = ''
            self.problem = ''
            self.pos = ''

    def add_child(self, child, start, end):
        self.children.append(child)
        child.parent = self
        child.start = start
        child.end = end

    def to_folia_sentence(self, doc, paragraph):
        sentence = paragraph.add(folia.Sentence)
        parts = []
        for c in self.children:
            parts.append((c.start, c.end, c))
        if not parts:
            parts.append((len(self.original), len(self.original), None))

        current_position = 0
        for p in parts:
            print p[0]
            tokens = tokenize(self.original[current_position:p[0]])
            for token in tokens:
                sentence.add(folia.Word, token)
            if p[2]:
                word = sentence.add(folia.Word)
                word.add(folia.Correction, folia.New(doc, p[2].edited), folia.Original(doc, p[2].original), cls=p[2].unit)

            current_position = p[1]
        tokens = tokenize(self.original[current_position:])
        for token in tokens:
            sentence.add(folia.Word, token)

    def __str__(self):
        result = '{} <{}>'.format(self.original, self.unit)
        #if not self.parent:
        #    result += '\nEdited: ' + self.edited
        for c in self.children:
            result += '\n\t' + str(c)
        return result


def match_outer(s):
    match = re.search(GREEDY_MATCH_TAG, s)
    if match:
        sentence = match.group(1)
        annotation = match.group(2)
        pa = PartAnnotation(sentence, annotation)
        extract_corrections(sentence, pa)
    else:
        print 'not found?'
    return pa


def match_inner(s, pa=None):
    matches = re.finditer(NON_GREEDY_MATCH_TAG, s)
    if not pa:
        pa = PartAnnotation(s, None)
    for match in matches:
        #print 'match', match.group(1), match.group(2)
        if match.start(0) == 0:
            sentence = match.group(1)
            annotation = match.group(2)
            pa = PartAnnotation(sentence, annotation)
        else:
            pa.add_child(PartAnnotation(match.group(1), match.group(2)), match.start(0), match.end(0))
    return pa


def extract_corrections(s, pa=None):
    if re.search(HAS_INNER, s):
        if pa is not None:
            print 'loop in loop! bug de bug'
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
    text = doc.append(folia.Text)
    paragraph = text.add(folia.Paragraph)
    with codecs.open('data/T1_VOWY0Q147044.txt', 'rb') as f:
        for n, line in enumerate(f):
            line = line.strip()
            if count_brackets(line):
                pa = extract_corrections(line)
                pa.to_folia_sentence(doc, paragraph)
                print pa
            else:
                print 'Number of brackets does not match on line', n
    doc.save('data/out.txt')


if __name__ == '__main__':
    process_file()
