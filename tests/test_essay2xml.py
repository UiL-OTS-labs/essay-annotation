import unittest

from conversions.essay2xml import has_inner, count_brackets, start_folia_document, process_line

class TestEssay2XML(unittest.TestCase):
    def test_has_inner(self):
        self.assertFalse(has_inner('[]'))
        self.assertTrue(has_inner('[[]]'))
        self.assertFalse(has_inner('[][]'))
        self.assertTrue(has_inner('[Het landschap in Nederland is vrij vlak en [het regent soms veel[/,]L*O soms weinig]I*W .]OT'))
        self.assertTrue(has_inner('Het landschap in Nederland is vrij vlak en [het regent soms veel[/,]L*O soms weinig]I*W .'))
        self.assertFalse(has_inner('het regent soms veel[/,]L*O soms weinig'))

    def test_count_brackets(self):
        self.assertFalse(count_brackets('[]]'))
        self.assertTrue(count_brackets('[[]]'))

    def test_corrections(self):
        doc = start_folia_document()
        line = '[Zwarte pieten/Zwarte Pieten]HN*O zijn zwart als [roed/roet]SPE*I*N [/.]L*O'
        process_line(line, doc)
        self.assertEqual(str(doc.sentences().next()), 'Zwarte Pieten zijn zwart als roet .')
