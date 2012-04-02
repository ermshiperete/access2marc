import csv
import pyodbc

from builder import MarcRecordBuilder
from builder import isRepeatableField

class Processor(object):

	def __init__(self, csvfile, dbconnstring):
		with open(csvfile, 'r') as f:
			reader = csv.DictReader(f)
			self.instructions = [row for row in reader]
		self._checkInstructions()
		self.conn = pyodbc.connect(dbconnstring)
		self.db = self.conn.cursor()
		self.items = dict()


	def LoadItemIDs(self):
		# query the db for a list of all item ids to extract
		for row in self.db.execute('SELECT Item.ItemID, Holding.HoldingID FROM Item LEFT JOIN Holding ON Item.ItemID = Holding.ItemID ORDER BY Item.ItemID'):
			if self.items.has_key(row.ItemID) and row.HoldingID not in self.items[row.ItemID]:
				self.items[row.ItemID].append(row.HoldingID)
			else:
				self.items[row.ItemID] = [row.HoldingID]


	def _checkInstructions(self):
		prevTag = None
		for line in self.instructions:
			currTag = line['Tag']
			if currTag == prevTag and isRepeatableField(currTag):
				print("Warning: Repeatable field %s should never have more than one line defined in the mapping" % currTag)

			prevTag = currTag


	def WriteMarcRecords(self, filename):
		#with codecs.open(filename, 'w', 'utf-8') as out:
		with open(filename, 'wb') as out:
			for id in self.items:
				builder = MarcRecordBuilder(id, self.items[id], self.instructions, self.db)
				rec = builder.GetMarcRecord()
				out.write(rec.as_marc())


if __name__ == '__main__':
	print('Running Access To Marc')

	# csv file, dbconnstring and output filename should all be command line options
	connstring = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=%s;Uid=%s;Pwd=%s" % (r'c:/src/access2marc/Setup MSEA lib catalog/libdata2.mdb', 'developer', 'r0ss')
	processor = Processor('c:/src/access2marc/data_map.csv', connstring)

	processor.LoadItemIDs()
	processor.WriteMarcRecords('c:/src/access2marc/output.marc')
	print('Finished')
