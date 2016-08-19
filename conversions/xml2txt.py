import codecs
import glob
import os

from pynlpl.formats import folia


def replace_specials(s):
    return s.replace(u' \u221A', '').replace(u' \u2205', '')


def process_file(filename):
    """
    Reads a single FoLiA .xml-file, loops over its Sentences,
    and writes the text to the csv file.
    """
    fname, _ = os.path.splitext(filename)

    with codecs.open(fname + '_orig.txt', 'wb', 'utf-8') as orig_file:
        with codecs.open(fname + '_corr.txt', 'wb', 'utf-8') as corr_file:
            doc = folia.Document(file=filename)

            for sentence in doc.sentences():
                try:
                    s_original = sentence.text(correctionhandling=folia.CorrectionHandling.ORIGINAL)
                    s_corrected = sentence.text(correctionhandling=folia.CorrectionHandling.CURRENT)
                except folia.NoSuchText:
                    s_original = ''
                    s_corrected = ''

                orig_file.write(replace_specials(s_original))
                orig_file.write('\n')

                corr_file.write(replace_specials(s_corrected))
                corr_file.write('\n')


def process_folder(folder):
    """
    Writes annotations from all FoLiA .xml-files from the given folder to .txt-files.
    """
    # Loop over all .xml-files in the given folder
    for filename in glob.glob(os.path.join(folder, '*.xml')):
        print 'Processing ', filename
        process_file(filename)

if __name__ == '__main__':
    process_folder('../data/out')
