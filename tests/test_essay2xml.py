# -*- coding: utf-8 -*-

import unittest

from pynlpl.formats import folia

from conversions.essay2xml import ParseException, count_brackets, start_folia_document, process_line, get_matching_brackets


class TestEssay2XML(unittest.TestCase):
    def test_count_brackets(self):
        with self.assertRaises(ParseException):
            count_brackets(0, '[]]')

    def test_corrections(self):
        doc = start_folia_document('test')
        line = '[Zwarte pieten/Zwarte Pieten]HN*O zijn zwart als [roed/roet]SPE*I*N [/.]L*O'
        process_line(1, line, doc)
        s = doc.sentences().next()
        self.assertTrue(s.corrections())
        self.assertEqual(sum(1 for _ in s.select(folia.Correction)), 3)  # there's 3 corrections in the sentence
        self.assertEqual(str(s), 'Zwarte Pieten zijn zwart als roet .')

    def test_2xml(self):
        doc = start_folia_document('test')
        line = u'[Over [√/het]W*O*L weer gesproken]VMT , verwacht niet te veel van de zomers in Nederland, want het regent er heel veel en het is maar weinig echt warm [√/.]L*O'
        process_line(1, line, doc)
        s = doc.sentences().next()
        self.assertTrue(s.corrections())
        self.assertEqual(sum(1 for _ in s.select(folia.Correction)), 3)  # there's 2 corrections in the sentence

    def test_get_outer(self):
        line = '[Over [√/het]W*O*L weer gesproken]VMT'
        matches = get_matching_brackets(line)
        self.assertEqual(matches[0], (0, 35))

        line = 'Het landschap in Nederland is vrij vlak en [het regent soms veel[/,]L*O soms weinig]I*W .'
        matches = get_matching_brackets(line)
        self.assertEqual(matches[0], (43, 83))

        line = '[Zwarte pieten/Zwarte Pieten]HN*O zijn zwart als [roed/roet]SPE*I*N [/.]L*O'
        matches = get_matching_brackets(line)
        self.assertEqual(matches[0], (0, 28))
        self.assertEqual(matches[1], (49, 59))
        self.assertEqual(matches[2], (68, 71))
