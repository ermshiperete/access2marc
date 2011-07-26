import csv
import pyodbc
import codecs
from builder import MarcRecordBuilder

class Processor(object):

	def __init__(self, csvfile, dbconnstring):
		with open(csvfile, 'r') as f:
			reader = csv.DictReader(f)
			self.instructions = [row for row in reader]
		self.conn = pyodbc.connect(dbconnstring)
		self.db = self.conn.cursor()


	def LoadItemIDs(self):
		# query the db for a list of all item ids to extract
		self.itemids = [
				row.ItemID for row in self.db.execute('SELECT ItemID FROM Item')]
				#row.ItemID for row in self.db.execute('SELECT ItemID FROM Item WHERE ItemID > 2502')]
				#row.ItemID for row in self.db.execute("SELECT ItemID FROM Item WHERE ItemID = 2502")]

	def WriteMarcRecords(self, filename):
		#with codecs.open(filename, 'w', 'utf-8') as out:
		with open(filename, 'wb') as out:
			for id in self.itemids:
				builder = MarcRecordBuilder(id, self.instructions, self.db)
				rec = builder.GetMarcRecord()
				out.write(rec.as_marc())


if __name__ == '__main__':
	print('Running Access To Marc')

	# csv file, dbconnstring and output filename should all be command line options
	connstring = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=%s;Uid=%s;Pwd=%s" % (r'Setup MSEA lib catalog\Library2forCM.mdb', 'developer', 'r0ss')
	processor = Processor('data_map.csv', connstring)

	processor.LoadItemIDs()
	processor.WriteMarcRecords('output.marc')
