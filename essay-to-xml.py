import codecs
import re

from pynlpl.formats import folia
from pynlpl.textprocessors import tokenize

HAS_INNER = re.compile(r'\[[^\]]*\[')
GREEDY_MATCH_TAG = re.compile(r'\[(.*)\](\w[\*\w]*)')
NON_GREEDY_MATCH_TAG = re.compile(r'\[(.*?)\](\w[\*\w]*)')


class MyCorrection(folia.Correction):
    """Allow Corrections to have second-order annotation"""
    ACCEPTED_DATA = folia.Correction.ACCEPTED_DATA + (folia.Feature,)


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
            self.annotation = None
            self.unit = None
            self.problem = None
            self.pos = None

    def add_child(self, child, start, end):
        self.children.append(child)
        child.parent = self
        child.start = start
        child.end = end

    def to_folia_sentence_child(self, doc, sentence):
        original = tokenize(self.original)
        edited = tokenize(self.edited)

        correction = None
        # If we're dealing with single words (e.g. spelling errors), create the correction directly on the word.
        if len(original) == 1 and len(edited) == 1:
            word = sentence.add(folia.Word)
            correction = word.add(MyCorrection, folia.New(doc, self.edited), folia.Original(doc, self.original), cls=self.unit)
        # We are dealing with more than one word, or an insertion/deletion. Create word elements for each token.
        else:
            new = folia.New(doc)
            orig = folia.Original(doc)
            for w in edited:
                new.add(folia.Word, w, generate_id_in=sentence)
            for w in original:
                orig.add(folia.Word, w, generate_id_in=sentence)

            correction = sentence.add(MyCorrection, new, orig, cls=self.unit)

        if self.problem:
            correction.add(folia.Feature, subset='problem', cls=self.problem)
        if self.pos:
            correction.add(folia.Feature, subset='pos', cls=self.pos)

    def to_folia_sentence(self, doc, paragraph):
        sentence = paragraph.add(folia.Sentence)
        parts = []
        # TODO: order the children by start position
        # TODO: deal with nesting here.
        for c in self.children:
            parts.append((c.start, c.end, c))
        parts.append((len(self.original), None, None))

        current_position = 0
        for start, end, child in parts:
            tokens = tokenize(self.original[current_position:start])
            for token in tokens:
                sentence.add(folia.Word, token)
            if child:
                child.to_folia_sentence_child(doc, sentence)
            current_position = end

        if self.unit:
            layer = sentence.add(folia.SemanticRolesLayer)
            layer.add(folia.SemanticRole(doc, cls=self.unit))

    def __str__(self):
        result = '{} <{}>'.format(self.original, self.unit)
        #if not self.parent:
        #    result += '\nEdited: ' + self.edited
        for c in self.children:
            result += '\n\t' + str(c)
        return result


def match_outer(s):
    # TODO: this does not work:
    # [Zwarte pieten/Zwarte Pieten]HN*O zijn zwart als [roed/roet]SPE*I*N [/.]L*O
    match = GREEDY_MATCH_TAG.search(s)
    if match:
        sentence = match.group(1)
        annotation = match.group(2)
        pa = PartAnnotation(sentence, annotation)
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
    doc.declare(folia.SemanticRolesLayer, 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/config/semanticroles.foliaset.xml')
    text = doc.append(folia.Text)
    paragraph = text.add(folia.Paragraph)
    with codecs.open('data/T1_VOWY0Q147044.txt', 'rb') as f:
        for n, line in enumerate(f):
            line = line.strip()
            if count_brackets(line):
                pa = extract_corrections(line)
                pa.to_folia_sentence(doc, paragraph)
                #print pa
            else:
                print 'Number of brackets does not match on line', n
    doc.save('data/out.txt')


if __name__ == '__main__':
    process_file()
