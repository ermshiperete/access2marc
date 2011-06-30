import csv
import pyodbc
import pymarc

class MarcRecordBuilder(object):
	def __init__(self, itemID, instructions, queryObject):
		self.ItemID = itemID
		self.qo = queryObject
		self.Fields = list()
		self.instructions = instructions
		self._build()

	def _build(self):
		# parse the instruction csv and divide it up into field instructions
		# a field instruction may contain multiple lines.  Fixed fields have one line per data element (which may span multiple chars) and Regular fields will have one line per subfield

		# populate the field builder list by chopping up the instructions
		while (self.Instructions ...):
			# if its a fixed field
			self.Fields.append(MarcFixedFieldBuilder(self.itemID, instructions, qo))

			# if its a normal field
			self.Fields.append(MarcFieldBuilder(self.itemID, instructions, qo))

		pass


	def GetMarcRecord(self):
		rec = pymarc.Record()
		for fieldbuilder in self.Fields:
			rec.add_field(fieldbuilder.GetMarcField())
		return rec




class MarcFixedFieldBuilder(object):

	def __init__(self, itemID, instructions, queryObject):
		self.ItemID = itemID
		self.DataChar = dict()
		self.Tag = ''
		self.qo = queryObject
		self.Instructions = instructions
		self._build()


	def _build(self):

		# get tag from first line
		self.Tag = self.Instructions[0]['Tag']

		for line in self.Instructions:
			(positions, data) = self._doQuery(line)

			# split data into characters
			for position, char in self._splitData(positions, data):
				self.DataChar[position] = char


	def _doQuery(self, line):
		# return positions and associated data
		pass


	def _splitData(self, positions, data):
		# return position and character
		pass


	def GetMarcField(self):
		data = ''
		for i in range(0..100):
			if i in self.DataChars:
				data += self.DataChar[i]
			else:
				data += ' '

		# trim fixed field based upon tag
		data = {
				'000': lambda d: d.rstrip(),
				'001': lambda d: d.rstrip(),
				'003': lambda d: d.rstrip(),
				'005': lambda d: d[:16],
				'007': lambda d: d[:23],
				'008': lambda d: d[:40]
				}[self.Tag](data)

		return pymarc.Field(self.Tag, data)







class MarcFieldBuilder(object):
	def __init__(self, itemID, instructions, queryObject):
		self.ItemID = itemID
		self.SubFields = list()
		self.Indicators = list()
		self.Tag = ''
		self.qo = queryObject
		self.Instructions = instructions
		self._build()


	def _build(self):
		# get tag from first line
		# this could be done in the constructor
		self.Tag = self.Instructions[0]['Tag']

		for line in self.Instructions:

			# basically just do this for the first line
			if (len(self.Indicators) == 0):
				self.Indicators.append(self._doI1Query(line))
				self.Indicators.append(self._doI2Query(line))

			self.SubFields.extend(self._doSubfieldQuery(line))


			# split data into characters
			for position, char in self._splitData(positions, data):
				self.DataChar[position] = char


	def _doI1Query(self, line):
		# return the indicator string
		pass


	def _doI2Query(self, line):
		# return the indicator string
		pass


	def _doSubFieldQuery(self, line):
		# if the 'subfield' column contains a subfield char, then
		# return a list in this format:
		# ['subfield', 'subfield data']

		# if the 'subfield' column contains the string 'inline',
		# then parse the result and make a list in the format:
		# ['subfield1', 'data1', 'subfield2', 'data2', ... ]
		pass


	def GetMarcField(self):
		return pymarc.Field(self.Tag, self.Indicators, self.SubFields)











class Processor(object):

	def __init__(self, xlsfile, dbalias):
		self.map = csv.DictReader(xslfile)
		self.conn = pyodbc.connect('DSN=%s')
		self.db = self.conn.cursor()

		# load SQL statements into a dictionary

		_prepSQL():


	def _preSQL(self):


	def getmarcforid(id):
		pass




class MarcFieldBase(object):

	def __init__(self, tag):
		self.tag = tag
		self.value = ''
		self.defaultvalue = ''
		self.select = ''
		self.from = ''
		self.where = ''
		self.end = ''


	def getSQL(self):
		return 'SELECT %s FROM %s WHERE %s %s' % (
				self.select,
				self.from,
				self.where,
				self.end
				)

	def runSQL



class MarcFixedField(MarcFieldBase):

	def __init__(self, tag, position):
		MarcFieldBase.__init__(self, tag)
		self.position = position
		pass



class MarcSubField(MarcFieldBase):

	def __init__(self, tag, position):
		MarcFieldBase.__init__(self, tag)
		self.position = position
