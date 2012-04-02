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


DEBUGMODE = False


class MarcRecordBuilder(Logger):
	def __init__(self, itemID, holdings, instructions, queryObject):
		Logger.__init__(self, sys.stdout, DEBUGMODE, 'RecBuild')
		self.ItemID = itemID
		self.HoldingIDs = holdings # a list of holdingIDs
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
			elif isHoldingField(tag):
				self.Fields.append(
						MarcHoldingsBuilder(self.ItemID, self.HoldingIDs, inst, self.qo))
			else: # regular field
				self.Fields.append(
						MarcFieldBuilder(self.ItemID, inst, self.qo))



		# populate the field builder list by chopping up the instructions
		currTag = ''
		currInstructions = []
		for row in self.Instructions:
			if not row['Tag']:
				continue

			# make sure Tag is in 3 digit format
			row['Tag'] = row['Tag'].zfill(3);

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
			builderType = type(fieldbuilder).__name__
			if builderType == 'MarcFixedFieldBuilder':
				field = fieldbuilder.GetMarcField()
				if field.tag == '000':
					self.Debug("000 value: '%s'" % field.value())
					self.Debug("Leader before: '%s'" % rec.leader)
					self._addToLeader(rec, field.value())
					self.Debug("Leader after: '%s'" % rec.leader)
				else:
					if len(field.data) > 0:
						rec.add_field(field)
			else: # MarcFieldBuilder # expecting list of fields
				fields = fieldbuilder.GetMarcField()

				for f in fields:
					if len(f.subfields) > 0:
						self.Debug("Adding Field %s for Item %s" % (f.tag, self.ItemID))
						self.Debug("subfields in %s are " % f.tag + str(f.subfields))
						rec.add_field(f)
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
		Logger.__init__(self, sys.stdout, DEBUGMODE, 'Query')
		self.qo = qo
		self.id = id

		self.map = dict()
		for e in line:
			# standardize on single quotes
			self.map[e] = line[e].replace('"', "'")


	def FetchData(self):
		# returns a list, in case this is a repeatable field
		qselect = "SELECT %s" % self.map['SQLSelect']
		return self._fetch(qselect)


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


	def FetchHolding(self, holdingID):
		# returns a dictionary of holdingID -> value in case a record has more than one holding
		qselect = "SELECT %s" % self.map['SQLSelect']
		qfrom = "FROM %s" % self.map['SQLFrom']
		qend = self.map['SQLEnd']
		witemid = "Item.ItemID = %s AND Holding.HoldingID = %s" % (self.id, holdingID)
		if self.map['SQLWhere'].strip():
			qwhere = "WHERE (%s) AND %s" % (self.map['SQLWhere'], witemid)
		else:
			qwhere = "WHERE %s" % witemid
		return self._execSQL(qselect, qfrom, qwhere, qend)


	def _fetch(self, qselect, customFuncEnd=''):
		qfrom = "FROM %s" % self.map['SQLFrom']
		witemid = "Item.ItemID = %s" % self.id
		if self.map['SQLWhere'].strip():
			qwhere = "WHERE (%s) AND %s" % (self.map['SQLWhere'], witemid)
		else:
			qwhere = "WHERE %s" % witemid
		qend = self.map['SQLEnd']
		return self._execSQL(qselect, qfrom, qwhere, qend, customFuncEnd)


	def _execSQL(self, qselect, qfrom, qwhere, qend, customFuncEnd=''):
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
					if customFuncEnd:
						customFuncEnd = '_' + customFuncEnd
					funccall = "custom.%s(row)" % (self.map['Python'] + customFuncEnd)
					try:
						result = eval(funccall)
						self.Debug("before %s = %s" % (funccall, str(row)))
						self.Debug("after %s = %s" % (funccall, result))
					except AttributeError, err:
						self.Debug(str(err))
						self.Debug("Notice: %s isn't defined in custom.py.  Skipping." % funccall)
				processedrows.append(result)
		return processedrows




class MarcFixedFieldBuilder(Logger):

	def __init__(self, itemID, instructions, queryObject):
		Logger.__init__(self, sys.stdout, DEBUGMODE, 'FFieldBuild')
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
				ctr = 0
				actualsize = len(data)
				for x in range(startpos, endpos + 1):
					if ctr < actualsize:
						datamap.append((x, data[ctr]))
					else:
						datamap.append((x, " "))
					ctr += 1
			else:
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
			dataToReturn = ""
			try:
				dataToReturn = str(data[0]).strip();
			except UnicodeEncodeError:
				dataToReturn = ""
			return (line['FFPosition'], dataToReturn)
		else:
			return (line['FFPosition'], "")




	def GetMarcField(self):
		data = ''
		for i in range(0, 100):
			pos = str(i)
			if pos in self.DataChar and self.DataChar[pos].strip() != '':
				data += self.DataChar[pos]
			else:
				data += ' '

		# trim fixed field based upon tag
		data = {
				'000': lambda d: d[:24], # 00-23
				'001': lambda d: d.rstrip(),
				'003': lambda d: d.rstrip(),
				'005': lambda d: d[:16],
				'007': lambda d: d[:23],
				'008': lambda d: d[:40] # 00-39
				}[self.Tag](data)

		pymarcfield = pymarc.Field(tag=self.Tag, data=data)
		return pymarcfield



class MarcFieldBuilder(Logger):
	def __init__(self, itemID, instructions, queryObject):
		Logger.__init__(self, sys.stdout, DEBUGMODE, 'SFieldBuild')
		self.ItemID = itemID
		self.SubFields = list() # eg. ['a', 'the title', 'c', 'the author']
		self.Indicators = list() # eg. ['0', '1']

		# get tag from first line
		self.Tag = instructions[0]['Tag']

		# A list of SubField lists, in the case
		# that this field is repeatable
		self.ListOfSubFields = list()

		self.qo = queryObject
		self.Instructions = instructions
		self._build()


	def _build(self):
		for line in self.Instructions:

			# basically just do this for the first line
			if (len(self.Indicators) == 0):
				self.Indicators.append(self._doIndicatorQuery(line, 1))
				self.Indicators.append(self._doIndicatorQuery(line, 2))

			self.Debug("%s%s = " % (self.Tag, line['Subfield']))
			if isRepeatableField(self.Tag):
				subfields = self._doSubfieldQuery(line)
				self.Debug(subfields)
				self.ListOfSubFields = subfields
			else:
				subfields = self._doSubfieldQuery(line)
				self.Debug(subfields)
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
		defaultValue = line['DefaultValue'].strip()
		if line['SQLSelect']:
			q = SQLQuery(self.qo, self.ItemID, line)

			# data is a list, in case there are repeatable subfields
			data = q.FetchData()

			if isRepeatableField(self.Tag):
			# if this MARC tag is a repeatable tag, then we treat each subfield line as a separate tag (e.g. 650)
				result = list()
				for item in data:
					if item:
						result.append(self._processSubfieldResult(subfield, item))
				return result

			# if this is a repeatable subfield, we want to process all data returned as subfields of this field
			elif line['SubfieldRepeatable'].lower().find('yes') > -1:
				result = list()
				for item in data:
					if item:
						result.extend(self._processSubfieldResult(subfield, item))
				return result

			# otherwise just process the first one returned (and warn if more than one returned)
			else:
				if len(data) > 1:
					self.Log("Warning: item_%s : field_%s : Expected 1 but SQL returned %s rows: %s" % (self.ItemID, self.Tag, len(data), str(data)))
					return self._processSubfieldResult(subfield, data[0])
				if len(data) > 0 and data[0] is not None and len(data[0]) > 0:
					return self._processSubfieldResult(subfield, data[0])
				if defaultValue:
					return (subfield, defaultValue)
				return ()

		elif defaultValue:
			# if there is a default value, use that
			return ( subfield, defaultValue )
		else:
			return ()



	def _processSubfieldResult(self, subfield, data):

		def _validSubfieldList(subfieldList):
			if len(subfieldList) % 2 == 0:
				return subfieldList # even number of items is valid
			# try to fix subfield list by removing duplicate items???
			prevItem = None
			newList = []
			for item in subfieldList:
				if item != prevItem:
					newList.append(item)
				prevItem = item
			return newList



		def _splitData(inlineString):
			state = 'DATA'
			result = []
			data = ""
			marker = ""
			for c in inlineString:
				#self.Debug("c = %s; state = %s; data = %s" % (c, state, data))
				if state == 'CODE':
					marker = c
					state = 'DATA'
					if data:
						result.append(data)
						data = ""

				elif state == 'DATA':
					if c == '$' or c == '|' or c == '^':
						state = 'CODE'
						continue
					if marker:
						result.append(marker)
						marker = ""
					data += c
			if data:
				result.append(data)
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
			dataToReturn = _splitData(data)
			return _validSubfieldList(dataToReturn)

		# error: could not get a valid subfield
		else:
			self.Log("Error: Could not understand subfield '%s' for tag %s" % (subfield, self.Tag))
			return ()


	def GetMarcField(self):
		listToReturn = []
		if isRepeatableField(self.Tag) or isHoldingField(self.Tag):
			for f in self.ListOfSubFields:
				if len(f) % 2 != 0:
					raise BuilderException("item_%s : tag_%s : Subfields list must contain pairs of subfield and it's value: %s" % (self.ItemID, self.Tag, str(f)))
				listToReturn.append(pymarc.Field(self.Tag, self.Indicators, f))
			return listToReturn
		else:
			if len(self.SubFields) % 2 != 0:
				raise BuilderException("item_%s : tag_%s : Subfields list must contain pairs of subfield and it's value: %s" % (self.ItemID, self.Tag, str(self.SubFields)))
			listToReturn.append(pymarc.Field(self.Tag, self.Indicators, self.SubFields))
			return listToReturn




class MarcHoldingsBuilder(MarcFieldBuilder):
	def __init__(self, itemID, holdingIDs, instructions, queryObject):
		Logger.__init__(self, sys.stdout, DEBUGMODE, 'HoldBuild')
		self.ItemID = itemID
		self.HoldingIDs = holdingIDs
		self.SubFields = list() # intentionally left empty and not used: only referenced in GetMarcFields

		# get tag from first line
		self.Tag = instructions[0]['Tag']

		# A list of SubField lists, since these are holdings and a title may have more than one holding
		# that this field is repeatable
		# eg. list of these lists: ['a', 'the title', 'c', 'the author']
		self.ListOfSubFields = list()

		self.qo = queryObject
		self.Instructions = instructions
		self._build()


	def _build(self):
		self.Indicators = [' ', ' ']

		for holdingID in self.HoldingIDs:
			subfields = list()
			for line in self.Instructions:
				self.Debug("%s:%s %s = " % (holdingID, self.Tag, line['Subfield']))

				# normally this just returns one subfield data, unless this is a repeatable subfield
				holdingResult = self._doHoldingQuery(holdingID, line)
				subfields.extend(holdingResult)
				self.Debug(holdingResult)
			self.ListOfSubFields.append(subfields)


	def _doHoldingQuery(self, holdingID, line):
		subfield = line['Subfield'].strip("$| ")
		defaultValue = line['DefaultValue'].strip()
		if line['SQLSelect']:
			q = SQLQuery(self.qo, self.ItemID, line)

			# data is a list, in case there are repeatable subfields
			data = q.FetchHolding(holdingID)

			# if this is a repeatable subfield, we want to process all data returned as subfields of this field
			if line['SubfieldRepeatable'].lower().find('yes') > -1:
				result = list()
				for item in data:
					if item:
						result.extend(self._processSubfieldResult(subfield, item))
				return result

			# otherwise just process the first one returned (and warn if more than one returned)
			else:
				if len(data) > 1:
					self.Log("Warning: item_%s : field_%s : Expected 1 but SQL returned %s rows: %s" % (self.ItemID, self.Tag, len(data), str(data)))
					return self._processSubfieldResult(subfield, data[0])
				if len(data) > 0 and data[0] is not None and len(data[0]) > 0:
					return self._processSubfieldResult(subfield, data[0])
				if defaultValue:
					return (subfield, defaultValue)
				return ()

		elif defaultValue:
			# if there is a default value, use that
			return ( subfield, defaultValue )
		else:
			return ()






# utility functions

def isRepeatableField(tag):
	repeatabletaglist = ('013', '015', '016', '017', '020', '022', '024', '025', '026', '027', '028', '032', '033', '034', '035', '037', '041', '046', '047', '048', '050', '051', '052', '055', '060', '061', '070', '071', '072', '074', '080', '082', '084', '085', '086', '088', '210', '222', '242', '246', '247', '255', '257', '258', '260', '264', '270', '300', '307', '321', '336', '337', '338', '340', '342', '343', '344', '345', '346', '347', '351', '352', '355', '362', '363', '365', '366', '377', '380', '381', '382', '383', '490', '500', '501', '502', '504', '505', '506', '508', '510', '511', '513', '515', '516', '518', '520', '521', '524', '525', '526', '530', '533', '534', '535', '536', '538', '540', '541', '542', '544', '545', '546', '547', '550', '552', '555', '556', '561', '562', '563', '565', '567', '580', '581', '583', '584', '585', '586', '588', '600', '610', '611', '630', '648', '650', '651', '653', '654', '655', '656', '657', '658', '662', '700', '710', '711', '720', '730', '740', '751', '752', '753', '754', '760', '762', '765', '767', '770', '772', '773', '774', '775', '776', '777', '780', '785', '786', '787', '800', '810', '811', '830', '843', '845', '850', '852', '853', '854', '855', '856', '863', '864', '865', '866', '867', '868', '876', '877', '878', '880', '886', '887')
	if tag in repeatabletaglist:
		return True
	else:
		return False

def isHoldingField(tag):
	holdingtags = ('952')
	if tag in holdingtags:
		return True
	else:
		return False


