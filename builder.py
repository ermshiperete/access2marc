import csv
import pyodbc
import pymarc

"Exceptions for the MarcBuilder classes"
class BuilderException(Exception):
	pass

class IndicatorInvalid(BuilderException):
	def __init__(self, m):
		self.message = m
	def __str__(self):
		return "Indicator data error: %s" % self.message



class MarcRecordBuilder(object):
	def __init__(self, itemID, instructions, queryObject):
		self.ItemID = itemID
		self.qo = queryObject
		self.Fields = list()
		self.Instructions = instructions
		self._build()

	def _build(self):
		# parse the instruction csv and divide it up into field instructions
		# a field instruction may contain multiple lines.  Fixed fields have one line per data element (which may span multiple chars) and Regular fields will have one line per subfield


		def appendField(tag, inst):
			if (int) tag < 10: # fixed field
				self.Fields.append(
						MarcFixedFieldBuilder(self.itemID, inst, self.qo))
			else: # regular field
				self.Fields.append(
						MarcFieldBuilder(self.itemID, inst, self.qo))



		# populate the field builder list by chopping up the instructions
		currTag = ''
		currInstructions = []
		for row in self.Instructions:
			if currTag != row['Tag']: # process previous instruction group
				if len(currInstructions) > 0:
					appendField(currTag, currInstructions)

				# reset variables
				currTag = row['Tag']
				currInstructions = []

			currInstructions.append(row)
		appendField(currTag, currInstructions)


	def GetMarcRecord(self):
		rec = pymarc.Record()
		for fieldbuilder in self.Fields:
			rec.add_field(fieldbuilder.GetMarcField())
		return rec



class SQLQuery(object):
	def __init__(self, qo, id, line):
		self.qo = qo
		self.id = id
		self.map = line


	def FetchOne(self):
		sqlselect = "SELECT %s as data" % self.map['SQLSelect']



class MarcFixedFieldBuilder(object):

	def __init__(self, itemID, instructions, queryObject):
		self.ItemID = itemID
		self.DataChar = dict()
		self.Tag = ''
		self.qo = queryObject
		self.Instructions = instructions
		self._build()


	def _build(self):

		def splitData(positions, data):
			datamap = []
			if positions.find('-') != -1:
				# multiple positions
				startpos = (int)positions[0:positions.index('-')]
				endpos = (int)positions[positions.index('-')+1:]
				if len(data) > endpos - startpos + 1:
					raise IndicatorInvalid(
							"expect size 1, was size %d" % len(data))
				ctr = 0
				for x in range(startpos, endpos + 1):
					datamap.append((x, data[ctr]))
					ctr += 1
			else:
				# single position
				if len(data) > 1:
					raise IndicatorInvalid(
							"expect size 1, was size %d" % len(data))
				datamap.append((positions, data))

			return datamap


		# get tag from first line
		self.Tag = self.Instructions[0]['Tag']

		for line in self.Instructions:
			# split data into characters
			for position, char in splitData(self._doQuery(line)):
				self.DataChar[position] = char


	def _doQuery(self, line):
		data = ''
		if line['SQLSelect']:

			q = new SQLQuery(self.qo, self.ItemID, line)
			row = q.FetchOne()
			data = row['Data'].strip()
		else:
			data = line['DefaultValue'].strip()

		# return position range and data
		return (line['FFPosition'], data)



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


