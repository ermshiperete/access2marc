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
		self.assertEqual("1983", Process008Date1(["c1983,1984"]))
		self.assertEqual("1947", Process008Date1(["c1947-8"]))
		self.assertEqual("1900", Process008Date1(["c[19??]"]))
		self.assertEqual("1942", Process008Date1(["c[1942]"]))

	def testProcess008Date2_Returns4DigitYearIfFound(self):
		self.assertEqual("", Process008Date2(["c1994.", ""]))
		self.assertEqual("1998", Process008Date2(["1994-", "1998"]))
		self.assertEqual("1998", Process008Date2(["1994-98", ""]))
		self.assertEqual("2000", Process008Date2(["c19??", "2000"]))
		self.assertEqual("2000", Process008Date2(["1990. 2000", ""]))
		self.assertEqual("2001", Process008Date2(["c2000-01", ""]))
		self.assertEqual("2001", Process008Date2(["2000-1", ""]))
		self.assertEqual("1984", Process008Date2(["c1983,1984", ""]))
		self.assertEqual("1948", Process008Date2(["c1947-8", ""]))
		self.assertEqual("1962", Process008Date2(["c1961,1962", ""]))
		self.assertEqual("", Process008Date2(["c[1990]", ""]))

	def testProcess856_CleansUpURL(self):
		self.assertEqual("http://library.asia.sil.org/e-resources/mseag/DigiData/495.992%20Kensiw%20(Maniq)/B10212.pdf", Process856([r"#D:\LibrData\DigiData\495.992 Kensiw (Maniq)\B10212.pdf#"]))
		self.assertEqual("http://library.asia.sil.org/e-resources/mseag/DigiData/572.598%20Haroi,Roglai,Chru,Cham%20anthropology/B01898.pdf", Process856([r"DigiData\572.598 Haroi,Roglai,Chru,Cham anthropology\B01898.pdf#DigiData/572.598%20Haroi,Roglai,Chru,Cham%20anthropology/B01898.pdf#"]))
		self.assertEqual("http://sealang.net/archives/mks/16-17.htm", Process856([r"http://sealang.net/archives/mks/16-17.htm"]))




if __name__ == '__main__':
	unittest.main()