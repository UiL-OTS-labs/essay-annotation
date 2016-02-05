import unittest

from pynlpl.formats import folia

from conversions.essay2xml import is_nested, count_brackets, start_folia_document, process_line


class TestEssay2XML(unittest.TestCase):
    def test_is_nested(self):
        self.assertFalse(is_nested('[]'))
        self.assertTrue(is_nested('[[]]'))
        self.assertFalse(is_nested('[][]'))
        self.assertTrue(is_nested('[Het landschap in Nederland is vrij vlak en [het regent soms veel[/,]L*O soms weinig]I*W .]OT'))
        self.assertTrue(is_nested('Het landschap in Nederland is vrij vlak en [het regent soms veel[/,]L*O soms weinig]I*W .'))
        self.assertFalse(is_nested('het regent soms veel[/,]L*O soms weinig'))

    def test_count_brackets(self):
        self.assertFalse(count_brackets('[]]'))
        self.assertTrue(count_brackets('[[]]'))

    def test_corrections(self):
        doc = start_folia_document('test')
        line = '[Zwarte pieten/Zwarte Pieten]HN*O zijn zwart als [roed/roet]SPE*I*N [/.]L*O'
        process_line(line, doc)
        s = doc.sentences().next()
        self.assertTrue(s.corrections())
        self.assertEqual(sum(1 for _ in s.select(folia.Correction)), 3)  # there's 3 corrections in the sentence
        self.assertEqual(str(s), 'Zwarte Pieten zijn zwart als roet .')
