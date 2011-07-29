import sys
import csv
import pyodbc
import pymarc
from logger import Logger
try:
	import custom
except SyntaxError as e:
	print("Bummer: It looks like there is a syntax error in the custom.py script file.  Custom functions are temporarily disabled.\nMessage: %s" % e)
	raise

"Exceptions for the MarcBuilder classes"
class BuilderException(Exception):
	pass

class IndicatorInvalid(BuilderException):
	def __init__(self, m):
		self.message = m
	def __str__(self):
		return "Indicator data error: %s" % self.message



class MarcRecordBuilder(Logger):
	def __init__(self, itemID, instructions, queryObject):
		Logger.__init__(self, sys.stdout, False, 'RecBuild')
		self.ItemID = itemID
		self.qo = queryObject
		self.Fields = list()
		self.Instructions = instructions
		self.Log("\nProcessing Record %s" % itemID)
		self._build()

	def _build(self):
		# parse the instruction csv and divide it up into field instructions
		# a field instruction may contain multiple lines.  Fixed fields have one line per data element (which may span multiple chars) and Regular fields will have one line per subfield


		def appendField(tag, inst):
			if int(tag) < 10: # fixed field
				self.Fields.append(
						MarcFixedFieldBuilder(self.ItemID, inst, self.qo))
			else: # regular field
				self.Fields.append(
						MarcFieldBuilder(self.ItemID, inst, self.qo))



		# populate the field builder list by chopping up the instructions
		currTag = ''
		currInstructions = []
		for row in self.Instructions:
			if not row['Tag']:
				continue

			if currTag != row['Tag']: # process previous instruction group
				if len(currInstructions) > 0:
					appendField(currTag, currInstructions)

				# reset variables
				currTag = row['Tag']
				currInstructions = []

			currInstructions.append(row)
		appendField(currTag, currInstructions)


	def GetMarcRecord(self):
		rec = pymarc.Record('', False, True) # force Unicode record
		for fieldbuilder in self.Fields:
			field = fieldbuilder.GetMarcField()
			if field.tag == '000':
				self.Debug("Leader before: '%s'" % rec.leader)
				self._addToLeader(rec, field.value())
				self.Debug("Leader after: '%s'" % rec.leader)
			elif field.tag < '010':
				if len(field.data) > 0:
					rec.add_field(field)
			else: # normal field having subfields
				if len(field.subfields) > 0:
					rec.add_field(field)
		return rec


	def _addToLeader(self, rec, incomingdata):
		# replace leader data char by char with input data
		leader = list(rec.leader)
		data = list(incomingdata)
		for index, char in enumerate(data):
			if char != ' ' and index < len(leader):
				leader[index] = char
		rec.leader = "".join(leader)





class SQLQuery(Logger):
	def __init__(self, qo, id, line):
		Logger.__init__(self, sys.stdout, False, 'Query')
		self.qo = qo
		self.id = id
		self.map = line


	def FetchData(self):
		qselect = "SELECT %s" % self.map['SQLSelect']
		return self._fetch(qselect, 'data')


	def FetchIndicator(self, indicator):
		key = "I%d_SQLSelect" % indicator
		if self.map[key] == "":
			return " "
		qselect = "SELECT %s" % self.map[key]
		result = self._fetch(qselect, 'indicator'+str(indicator))
		if len(result) > 0:
			return result[0]
		else:
			return " "


	def _fetch(self, qselect, mode='data'):
		qfrom = "FROM %s" % self.map['SQLFrom']
		witemid = "Item.ItemID = %s" % self.id
		if self.map['SQLWhere'].strip():
			qwhere = "WHERE (%s) AND %s" % (self.map['SQLWhere'], witemid)
		else:
			qwhere = "WHERE %s" % witemid
		qend = self.map['SQLEnd']
		sql = "%s %s %s %s" % (qselect, qfrom, qwhere, qend)
		self.Debug(sql)
		try:
			self.qo.execute(sql)
			rows = self.qo.fetchall()
		except pyodbc.Error as e:
			self.Log("\n\nAccessDB Error:\n\t%s" % e[1])
			if not self.verbose:
				self.Log("\nOffending statement:\n\t%s\n" % sql)
			rows = []

		processedrows = []
		for row in rows:
			if row and len(row) > 0 and row[0] is not None:
				result = unicode(row[0]).strip()
				if 'custom' in sys.modules and self.map['Python']:
					funcend = ""
					if mode != 'data':
						funcend = "_" + mode
					funccall = "custom.%s(row)" % (self.map['Python'] + funcend)
					try:
						result = eval(funccall)
						self.Debug("before %s = %s" % (funccall, str(row)))
						self.Debug("after %s = %s" % (funccall, result))
					except AttributeError:
						self.Debug("Warning: %s isn't defined in custom.py.  Skipping." % funccall)
				processedrows.append(result)
		return processedrows




class MarcFixedFieldBuilder(Logger):

	def __init__(self, itemID, instructions, queryObject):
		Logger.__init__(self, sys.stdout, False, 'FFieldBuild')
		self.ItemID = itemID
		self.DataChar = dict()

		# get tag from first line
		self.Tag = instructions[0]['Tag']

		self.qo = queryObject
		self.Instructions = instructions
		self._build()


	def _build(self):

		def splitData(positions, data):
			datamap = []
			if positions.find('-') != -1:
				# multiple positions
				startpos = int(positions[0:positions.index('-')])
				endpos = int(positions[positions.index('-')+1:])
				expectedlen = endpos - startpos + 1
				#if len(data) != expectedlen:
				#    self.Debug("Indicator Length Warning: expected %d, was %d" % (
				#        expectedlen, len(data)))

				ctr = 0
				#expectedsize = endpos - startpos + 1
				actualsize = len(data)
				for x in range(startpos, endpos + 1):
					if ctr < actualsize:
						datamap.append((x, data[ctr]))
					else:
						datamap.append((x, " "))
					ctr += 1
			else:
				# single position
				#if len(data) != 1:
				#    self.Debug("Indicator Length Error: expected 1, was %d" % (
				#            len(data)))
				datamap.append((positions, data))
			return datamap


		for line in self.Instructions:
			positions, data = self._doQuery(line)
			self.Debug("fixed field %s (%s) = %s" % (self.Tag, positions, data))

			# split data into characters
			for position, char in splitData(positions, data):
				self.DataChar[position] = char


	def _doQuery(self, line):
		data = ''
		if line['SQLSelect']:

			q = SQLQuery(self.qo, self.ItemID, line)
			data = q.FetchData()
		else:
			data = line['DefaultValue'].strip()

		# return position range and data
		if len(data) > 0:
			return (line['FFPosition'], str(data[0]).strip())
		else:
			return (line['FFPosition'], "")




	def GetMarcField(self):
		data = ''
		for i in range(0, 100):
			if i in self.DataChar:
				#self.Debug("%02d = '%s'" % (i, self.DataChar[i]))
				data += self.DataChar[i]
			else:
				data += ' '

		# trim fixed field based upon tag
		data = {
				'000': lambda d: d[:25],
				'001': lambda d: d.rstrip(),
				'003': lambda d: d.rstrip(),
				'005': lambda d: d[:16],
				'007': lambda d: d[:23],
				'008': lambda d: d[:40]
				}[self.Tag](data)

		#self.Debug("%s = '%s'" % (self.Tag, data))
		return pymarc.Field(tag=self.Tag, data=data)




class MarcFieldBuilder(Logger):
	def __init__(self, itemID, instructions, queryObject):
		Logger.__init__(self, sys.stdout, False, 'SFieldBuild')
		self.ItemID = itemID
		self.SubFields = list() # eg. ['a', 'the title', 'c', 'the author']
		self.Indicators = list() # eg. ['0', '1']

		# get tag from first line
		self.Tag = instructions[0]['Tag']

		self.qo = queryObject
		self.Instructions = instructions
		self._build()


	def _build(self):

		for line in self.Instructions:

			# basically just do this for the first line
			if (len(self.Indicators) == 0):
				self.Indicators.append(self._doIndicatorQuery(line, 1))
				self.Indicators.append(self._doIndicatorQuery(line, 2))

			subfields = self._doSubfieldQuery(line)
			self.Debug("Subfield %s%s = " % (self.Tag, line['Subfield']))
			self.SubFields.extend(subfields)



	def _doIndicatorQuery(self, line, indicator):
		key = "I%d_SQLSelect" % indicator
		query = line[key]
		if query:

			# just return the raw value, since there actually isn't a query
			if len(query) == 1:
				return query

			q = SQLQuery(self.qo, self.ItemID, line)
			return q.FetchIndicator(indicator)

		else:
			# empty indicator
			return ' '



	def _doSubfieldQuery(self, line):
		subfield = line['Subfield'].strip("$| ")
		if line['SQLSelect']:
			q = SQLQuery(self.qo, self.ItemID, line)

			# data is a list, in case there are repeatable subfields
			data = q.FetchData()

			# if this is a repeatable field, we want to process all results
			if line['Repeatable'].lower().find('yes') > -1:
				result = list()
				for item in data:
					if item:
						result.extend(self._processSubfieldResult(subfield, item))
				return result

			# otherwise just process the first one returned (and warn if more than one returned)
			else:
				if len(data) > 1:
					self.Debug("Warning: Expected 1 but SQL returned %s rows" % len(data))
				if len(data) > 0 and data[0] is not None and len(data[0]) > 0:
					return self._processSubfieldResult(subfield, data[0])
				else:
					return ()

		elif line['DefaultValue'].strip():
			# if there is a default value, use that
			return ( subfield, line['DefaultValue'].strip() )
		else:
			return ()



	def _processSubfieldResult(self, subfield, data):
		def _splitData(data):
			# state machine
			state = 'DATA'
			result = ()
			data = ""
			for c in data:
				if state == 'FIELD':
					result.append(c)
					state = 'DATA'

				elif state == 'DATA':
					if c == '$' or c == '|':
						if data:
							result.append(data)
							data = ""
						state = 'FIELD'
						continue
					data += c
			return result


		# if the 'subfield' column contains a subfield char, then
		# return a list in this format:
		# ['subfield', 'subfield data']
		if len(subfield) == 1:
			return (subfield, data)

		# if the 'subfield' column contains the string 'inline',
		# then parse the result and make a list in the format:
		# ['subfield1', 'data1', 'subfield2', 'data2', ... ]
		elif subfield == 'inline':
			return _splitData(data)

		# error: could not get a valid subfield
		else:
			return ()





	def GetMarcField(self):
		return pymarc.Field(self.Tag, self.Indicators, self.SubFields)
