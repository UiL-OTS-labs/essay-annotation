import codecs
import glob
import os
import re

from pynlpl.formats import folia

from models import PartAnnotation

CORRECTIONS_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/master/config/corrections.foliaset.xml'
SEMANTICROLES_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/master/config/semanticroles.foliaset.xml'
WHITESPACE_SET = 'https://raw.githubusercontent.com/UiL-OTS-labs/essay-annotation/master/config/whitespace.foliaset.xml'

TAG = re.compile(r'(\w[\*\+\w]*)')


def extract_annotations(s, pa=None):
    """
    Extracts all annotations from a (plain text) sentence.
    """
    if not pa:
        pa = PartAnnotation(s, None)

    for start, end in get_matching_brackets(s):
        sentence = s[start+1:end]
        post_sentence = s[end+1:]

        annotation_match = TAG.match(post_sentence)
        annotation = annotation_match.group(1)

        p_child = PartAnnotation(sentence, annotation)
        pa.add_child(p_child, start, end + annotation_match.end(1) + 1)

        # Recurse into the annotation to find other annotations
        p_child = extract_annotations(sentence, p_child)

    return pa


def get_matching_brackets(s):
    """
    Finds the outer annotations in a sentence.
    """
    matches = []
    open_brackets = 0
    for n, c in enumerate(s):
        if c == '[':
            open_brackets += 1
            if open_brackets == 1:
                start = n
        if c == ']':
            open_brackets -= 1
            if open_brackets == 0:
                end = n
                matches.append((start, end))
    return matches


def count_brackets(n, line):
    """
    Matches the number of brackets on a line.
    """
    if line.count('[') != line.count(']'):
        print 'Number of brackets does not match on line', n
        return False
    return True


def check_no_annotation(n, line):
    """
    Check if there's a bracket without annotation.
    """
    if '] ' in line:
        print 'No annotation specified on line', n
        return False
    return True


def start_folia_document(filename):
    """
    Creates a FoLiA document, declares the annotation types and adds a Text and Paragraph.
    TODO: set correct metadata.
    """
    doc = folia.Document(id=filename)
    doc.declare(folia.Correction, CORRECTIONS_SET, annotatortype=folia.AnnotatorType.MANUAL)
    doc.declare(folia.SemanticRole, SEMANTICROLES_SET, annotatortype=folia.AnnotatorType.MANUAL)
    doc.declare(folia.Whitespace, WHITESPACE_SET, annotatortype=folia.AnnotatorType.MANUAL)
    doc.metadata = folia.NativeMetaData(score='88', time='3', words='110')  # TODO: set this correctly
    text = doc.append(folia.Text)
    text.add(folia.Paragraph)
    return doc


def process_line(line, doc):
    """
    Processes a single line from the plain-text annotation and converts that to a FoLiA Sentence.
    """
    # Strip the line and create a PartAnnotation structure
    line = line.strip()
    pa = extract_annotations(line)

    # Convert the PartAnnotation structure to a FoLiA Sentence
    current_paragraph = doc.paragraphs().next()
    roles = []
    if not pa.original and not pa.edited:
        whitespace = pa.to_folia_whitespace(doc, current_paragraph)
        current_paragraph.add(whitespace)
    # Create a new sentence in the document
    else:
        sentence = current_paragraph.add(folia.Sentence)
        _, roles = pa.to_folia_sentence(doc, sentence)

    # Add all collected roles to the SemanticRolesLayer
    if roles:
        layer = sentence.add(folia.SemanticRolesLayer)
        for role in roles:
            layer.add(role)


def process_file(dirname, filename):
    """
    Processes a plain-text annotation file and converts that to FoLiA XML.
    """
    with codecs.open(filename, 'rb') as f:
        print 'Processing', filename
        base = os.path.splitext(os.path.basename(filename))[0]
        doc = start_folia_document(base)
        for n, line in enumerate(f):
            count_brackets(n, line)
            check_no_annotation(n, line)
            process_line(line, doc)
        doc.save(dirname + '/out/' + base + '.xml')


def process_folder(dirname):
    """
    Processes a whole folder of plain-text annotation files.
    """
    for filename in glob.glob(dirname + '/*.txt'):
        process_file(dirname, filename)


if __name__ == '__main__':
    process_folder('../data')
