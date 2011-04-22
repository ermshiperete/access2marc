import csv
import pyodbc
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
