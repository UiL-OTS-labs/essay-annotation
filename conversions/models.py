from pynlpl.formats import folia
from pynlpl.textprocessors import tokenize


class MySemanticRole(folia.SemanticRole):
    ACCEPTED_DATA = folia.SemanticRole.ACCEPTED_DATA + (folia.Feature,)


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
            self.original = parts[0]
            self.edited = parts[1]
            self.is_correction = True
        else:
            self.original = part
            self.edited = None
            self.is_correction = False

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
            role = MySemanticRole(doc, *words, cls=self.unit)
            # TODO: not yet allowed
            self.add_features(role)
        return words, role

    def add_features(self, obj):
        """
        Optiionally adds features to the given FoLiA object.
        """
        if self.problem:
            obj.add(folia.Feature, subset='problem', cls=self.problem)
        if self.pos:
            obj.add(folia.Feature, subset='pos', cls=self.pos)

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
            n = folia.New(doc, self.edited)
            o = folia.Original(doc, self.original)
            correction = w.add(folia.Correction, n, o, cls=self.unit, generate_id_in=sentence)
            words.append(w)
        # We are dealing with more than one word, or an insertion/deletion. Create word elements for each token.
        else:
            n = folia.New(doc)
            o = folia.Original(doc)
            for w in edited_tokens:
                word = n.add(folia.Word, w, generate_id_in=sentence)
                words.append(word)
            for w in original_tokens:
                o.add(folia.Word, w, generate_id_in=sentence)
            correction = sentence.add(folia.Correction, n, o, cls=self.unit, generate_id_in=sentence)

        # Add the problem and/or pos feature.
        self.add_features(correction)

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

        # Special case for empty sentences
        if not all_words:
            word = sentence.add(folia.Word)
            all_words.append(word)

        # If this node has a unit, add a role.
        if self.unit:
            role = MySemanticRole(doc, *all_words, cls=self.unit)
            self.add_features(role)
            all_roles.append(role)

        return all_words, all_roles

    def __str__(self):
        result = '{} <{}*{}>'.format(self.original, self.unit, self.problem)
        #if not self.parent:
        #    result += '\nEdited: ' + self.edited
        for c in self.children:
            result += '\n\t' + str(c)
        return result
