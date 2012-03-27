import unittest
from builder import MarcFixedFieldBuilder

class QueryObjectForTest(object):
	results = list()
	query = ""
	result = list()

	def execute(self, query):
		if query in self.results:
			self.result = self.results[query]
		else:
			self.result = []

	def fetchall(self):
		return result

	def __init__(self):
		self.results = list()

	# query: string
	# result: list of rows (which a row is also a list)
	def addQuery(self, query, result):
		self.results[query] = result


class marcFixedFieldBuilderTest(unittest.TestCase):
	instructions = list()  # instructions are a list of dictionaries

	def setUp(self):
		unittest.TestCase.setUp(self)

	def testGetMarcField_position18DefaultValue_ValueIsIn18Position(self):
		row = {"Tag":"000",
			   "FFPosition":"18",
			   "DefaultValue":"a",
			   "SQLSelect":"",
			   "SQLFrom":"",
			   "SQLWhere":"",
			   "SQLEnd":"",
			   "Python":"",
			   "SubfieldRepeatable":"No"}
		self.instructions.append(row)
		builder = MarcFixedFieldBuilder("someID", self.instructions, QueryObjectForTest())
		field = builder.GetMarcField()
		self.assertEqual("                  a     ", field.value())


	def testGetMarcField_position18DefaultValueAndEmptyDataBeforeIt_ValueIsIn18Position(self):
		row = {"Tag":"000",
			   "FFPosition":"17",
			   "DefaultValue":"",
			   "SQLSelect":"",
			   "SQLFrom":"",
			   "SQLWhere":"",
			   "SQLEnd":"",
			   "Python":"",
			   "SubfieldRepeatable":"No"}
		self.instructions.append(row)
		row = {"Tag":"000",
			   "FFPosition":"18",
			   "DefaultValue":"a",
			   "SQLSelect":"",
			   "SQLFrom":"",
			   "SQLWhere":"",
			   "SQLEnd":"",
			   "Python":"",
			   "SubfieldRepeatable":"No"}
		self.instructions.append(row)
		builder = MarcFixedFieldBuilder("someID", self.instructions, QueryObjectForTest())
		field = builder.GetMarcField()
		self.assertEqual("                  a     ", field.value())