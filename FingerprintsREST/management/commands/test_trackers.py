from optparse import make_option
import pickle
from django.core.management.base import BaseCommand, CommandError
from FingerprintsREST.views.MatchLocation.Learning import generateData, generateModel, ScikitModel


class Command(BaseCommand):
    args = 'building'
    help = """Dumps a csv of the building specified to standard out"""

    option_list = BaseCommand.option_list + (
        make_option('--test', '-t',
                    action='store',
                    dest='test',
                    default=False,
                    help="""Test the model"""),
        make_option('--use-pickled-data', '-p',
                    action='store',
                    dest='pickle',
                    default=False,
                    help="""Use pickled data"""),
        make_option('--csv', '-c',
                    action='store_true',
                    dest='csv',
                    default=False,
                    help="""Print a CSV."""),
    )

    def handle(self, *args, **options):
        try:
            building = args[0]
            if options['pickle']:
                column_name_to_index, rows, classes, rooms, null_value, recent = pickle.load(open(options['pickle']))
                model = ScikitModel(rows, classes, rooms, column_name_to_index, null_value, recent)
            if options['test']:
                n = int(options['test'])
                print "Top " + str(n) + " testing for " + building
                hits = 0
                misses = 0
                if not options['pickle']:
                    model = generateModel(building, -1)
                print "model generated,", len(model.data), "rows"
                for row_index, row in enumerate(model.data):
                    if row_index % 50 == 0 and row_index > 0:
                        print row_index, "done, hits: ", hits, "misses: ", misses
                    possibilities = model.predictor.predict(row)
                    actual_class = model.predictor.classes_[row_index]
                    if actual_class in possibilities[:]:
                        hits += 1
                    else:
                        misses += 1
                print "HITS: "+str(hits)
                print "MISSES: "+str(misses)
                print "NUMBER OF CLASSES" + str(len(set(model.predictor.classes_)))
            if options['csv']:
                if not options['pickle']:
                    column_name_to_index, rows, classes, rooms, null_value, recent = generateData(building, -1)
                    f = open(building+" data.pickle", 'w')
                    pickle.dump((column_name_to_index, rows, classes, rooms, null_value, recent), f)
                    f.close()
                column_index_to_name = dict(((v,k) for k,v in column_name_to_index.iteritems()))
                print "CSV for "+building
                print "NULL value is "+str(null_value)
                for colindex in range(len(column_name_to_index)):
                    header = column_index_to_name[colindex]
                    print str(header) + ", ",
                print "Location_PK"
                for row_index, row in enumerate(rows):
                    for element in row:
                        print str(element) +", ",
                    print classes[row_index]
            if not (options['test'] or options['csv']):
                raise CommandError("No argument specified... please choose one of --test, --csv or both")
        except:
            import traceback
            traceback.print_exc(file=self.stderr)
