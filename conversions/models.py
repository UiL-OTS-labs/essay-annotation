from pynlpl.formats import folia
from pynlpl.textprocessors import tokenize


class PartAnnotation():
    def __init__(self, part, annotation):
        self.split_part(part)
        self.split_annotation(annotation)
        self.parent = None
        self.children = []
        self.start = 0
        self.end = len(self.original)

    def split_part(self, part):
        if '/' in part and '[' not in part:
            parts = part.split('/')
            self.original = parts[0] if parts[0] else u'\u221A'
            self.edited = parts[1] if parts[1] else u'\u2205'
            self.is_correction = True
        else:
            self.original = part
            self.edited = None
            self.is_correction = False

    def split_annotation(self, annotation):
        """
        Splits an annotation into a list of annotations.
        """
        self.annotations = []
        if annotation:
            for a in annotation.split('+'):
                a_part = a.split('*')
                unit = a_part[0]
                problem = a_part[1] if len(a_part) >= 2 else None
                pos = a_part[2] if len(a_part) == 3 else None
                self.annotations.append({'unit': unit, 'problem': problem, 'pos': pos})

    def add_child(self, child, start, end):
        self.children.append(child)
        child.parent = self
        child.start = start
        child.end = end

    def get_child_nodes(self):
        """
        Returns the start and end positions of the children nodes as a list of tuples.
        """
        parts = []
        for child in sorted(self.children, key=lambda c: c.start):
            child_part = (child.start, child.end, child)
            parts.append(child_part)
        return parts

    def to_folia_sentence_child(self, doc, sentence):
        words = []
        role = None
        if self.is_correction:
            words.extend(self.add_folia_correction(doc, sentence))
        else:
            for token in tokenize(self.original):
                w = sentence.add(folia.Word, token)
                words.append(w)
            for a in self.annotations:
                role = folia.SemanticRole(doc, *words, cls=a['unit'])
                self.add_features(role, a)
        return words, role

    def add_features(self, obj, annotation):
        """
        Optiionally adds features to the given FoLiA object.
        """
        if annotation['problem']:
            obj.add(folia.Feature, subset='problem', cls=annotation['problem'])
        if annotation['pos']:
            obj.add(folia.Feature, subset='pos', cls=annotation['pos'])

    def add_folia_correction(self, doc, sentence):
        """
        Adds a folia.Correction to an existing folia.Sentence. Output the created folia.Words.
        """
        words = []

        # Tokenize both the original and the edited form.
        original_tokens = tokenize(self.original)
        edited_tokens = tokenize(self.edited)

        # If we're dealing with single words (e.g. spelling errors), create the correction directly on the word.
        if len(original_tokens) == 1 and len(edited_tokens) == 1:
            w = sentence.add(folia.Word)
            words.append(w)
            n = folia.New(doc, self.edited)
            o = folia.Original(doc, self.original)
            for i, a in enumerate(self.annotations):
                if i == 0:
                    correction = w.add(folia.Correction, n, o, cls=a['unit'], generate_id_in=sentence)
                else:
                    n_new = folia.New(doc, self.edited)
                    o_new = folia.Original(doc, self.original)
                    correction = o.add(folia.Correction, n_new, o_new, cls=a['unit'], generate_id_in=sentence)
                self.add_features(correction, a)
        # We are dealing with more than one word, or an insertion/deletion. Create word elements for each token.
        else:
            n = folia.New(doc)
            o = folia.Original(doc)
            for w in edited_tokens:
                word = n.add(folia.Word, w, generate_id_in=sentence)
                words.append(word)
            for w in original_tokens:
                o.add(folia.Word, w, generate_id_in=sentence)
            for i, a in enumerate(self.annotations):
                if i == 0:
                    correction = sentence.add(folia.Correction, n, o, cls=a['unit'], generate_id_in=sentence)
                else:
                    n_new = folia.New(doc)
                    o_new = folia.Original(doc)
                    for w in edited_tokens:
                        n_new.add(folia.Word, w, generate_id_in=sentence)
                    for w in original_tokens:
                        o_new.add(folia.Word, w, generate_id_in=sentence)
                    correction = o.add(folia.Correction, n_new, o_new, cls=a['unit'], generate_id_in=sentence)
                self.add_features(correction, a)

        return words

    def to_folia_sentence(self, doc, sentence):
        all_words = []
        all_roles = []

        # Loop over the child nodes
        current_position = 0
        for start, end, node in self.get_child_nodes():
            # Add tokens until the start of the next child node to the sentence
            tokens = tokenize(self.original[current_position:start])
            for token in tokens:
                word = sentence.add(folia.Word, token)
                all_words.append(word)
            # If the child node has children, recurse
            if node.children:
                words, roles = node.to_folia_sentence(doc, sentence)
                all_words.extend(words)
                all_roles.extend(roles)
            # Else, add the child node
            else:
                words, role = node.to_folia_sentence_child(doc, sentence)
                all_words.extend(words)
                if role:
                    all_roles.append(role)
            current_position = end

        # Add the tokens from the last child node to the end of this node
        tokens = tokenize(self.original[current_position:self.end])
        for token in tokens:
            word = sentence.add(folia.Word, token)
            all_words.append(word)

        # If this node has annotations, add roles.
        for a in self.annotations:
            role = folia.SemanticRole(doc, *all_words, cls=a['unit'])
            self.add_features(role, a)
            all_roles.append(role)

        return all_words, all_roles

    def to_folia_whitespace(self, doc, paragraph):
        whitespace = folia.Whitespace(doc, generate_id_in=paragraph)
        if self.annotations:
            # TODO: more than one annotation not allowed?
            a = self.annotations[0]
            whitespace.cls = a['unit']
            self.add_features(whitespace, a)
        return whitespace

    def __str__(self):
        result = '{} <{}>'.format(self.original, self.annotations)
        for c in self.children:
            result += '\n\t' + str(c)
        return result
