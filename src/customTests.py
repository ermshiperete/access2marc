import unittest

from custom import *

class customTest(unittest.TestCase):

	def setUp(self):
		unittest.TestCase.setUp(self)

	def testProcess245a_FormatsCorrectly(self):
		titleonly = "A book title"
		titlewithauthor = "A book title: by yours truly"
		statement = "some statement"
		self.assertEqual("A book title", Process245a([titleonly, ""]))
		self.assertEqual("A book title:", Process245a([titlewithauthor, ""]))
		self.assertEqual("A book title /", Process245a([titleonly, statement]))

	def testProcess008Date1_Returns4DigitYear(self):
		self.assertEqual("1994", Process008Date1(["c1994."]))
		self.assertEqual("1994", Process008Date1(["1994-"]))
		self.assertEqual("1994", Process008Date1(["1994-98"]))
		self.assertEqual("1900", Process008Date1(["c19"]))
		self.assertEqual("2005", Process008Date1(["05-07"]))
		self.assertEqual("1977", Process008Date1(["77-80"]))

	def testProcess008Date2_Returns4DigitYearIfFound(self):
		self.assertEqual("", Process008Date2(["c1994.", ""]))
		self.assertEqual("1998", Process008Date2(["1994-", "1998"]))
		self.assertEqual("1998", Process008Date2(["1994-98", ""]))
		self.assertEqual("2000", Process008Date2(["c19??", "2000"]))
		self.assertEqual("2000", Process008Date2(["1990. 2000", ""]))
		self.assertEqual("2007", Process008Date2(["05-07", ""]))
		self.assertEqual("1980", Process008Date2(["77-80", ""]))
		self.assertEqual("2001", Process008Date2(["c2000-01", ""]))
		self.assertEqual("2001", Process008Date2(["2000-1", ""]))




if __name__ == '__main__':
	unittest.main()