import unicodecsv


class UnicodeCsvWriter(object):
    def _write(self, iterable, output_file):
        writer = unicodecsv.writer(output_file, encoding='utf-8')
        for row in iterable:
            writer.writerow(row)

    def write(self, iterable, filename='output.csv', mode='a'):
        with open(filename, mode=mode) as output:
            self._write(iterable, output)
