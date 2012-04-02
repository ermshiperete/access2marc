# define custom functions here for use in processing SQL output

import re
import urllib

def IllustrativeMatterCode(row):
	data = row[0]
	if data.find("ill.") > -1:
		return "a"
	if data.find("map") > -1:
		return "b"
	return "" # fallback


def IllustrativeMatterCode2(row):
	data = row[0]
	if data.find("map") > -1:
		return "b"
	return "" # fallback


def ItemNoteCode(row):
	data = row[0]
	if data.find("index") > -1:
		return "1"
	return "" # fallback

#def MainEntryPersonalName_indicator1(data):
#    if data.lower().find("forename") > -1:
#        return "0"
#    elif data.lower().find("surname") > -1:
#        return "1"
#    elif data.lower().find("family name") > -1:
#        return "3"
#    return "" # fallback

def MainEntryPersonalName(row):
	firstname = row[0]
	lastname = row[1]
	fullname = row[2]
	year = row[3]
	formofentry = row[4]
	if not formofentry:
		formofentry = '1'
	result = "$a"
	if formofentry == '0':
		if firstname:
			result += firstname.strip(",.")
		if lastname:
			result += " " + lastname.strip(",.")
	else:
		if lastname:
			result += lastname.strip(",.")
		if firstname:
			result += ", " + firstname.strip(",.") + "."
	if fullname:
		result += " $q(%s)" % fullname.strip()
	if year:
		result += " $d%s" % year.strip
	return result


def Process245a(row):
	""" Custom function to provide appropriate formatting around the
	MARC 245a field (the main title)

	If the title has a : in it, then return the first part with the :
	>>> Process245a(['A book title: Joe Author.', 'statement'])
	'A book title:'

	If the title doesn't have a : (there is not author), then insert a slash
	if there is a statement of responsibility present
	>>> Process245a(['A book title without a colon', 'statement'])
	'A book title without a colon /'

	If a title has no colon and no statement following it,
	don't add anything extra
	>>> Process245a(['A book title', ''])
	'A book title'
	"""
	title = row[0]
	statement = row[1]
	if title.find(':') > -1:
		return title[0:title.index(':')+1]
	else:
		if statement is not None and statement != '':
			return title + ' /' # add slash for expected statement of resp.
		else:
			return title


def Process245b(row):
	title = row[0]
	statement = row[1]
	returnval = ""
	if title.find(':') > -1:
		if statement is not None and statement != '':
			returnval = title[title.index(':')+1:] + ' /' # slash for statement of resp.
		else:
			returnval = title[title.index(':')+1:]
	else:
		returnval = ""
	return returnval.strip()

REGEX008DATE = re.compile(r'(\d+)(\D+)?(\d+)?')
REGEX856URL = re.compile(r'#(.+)#')

def Process008Date1(row):
	date = row[0]
	m = REGEX008DATE.search(date)
	if m:
		return str(m.group(1)).ljust(4, '0') # fill out year with zeros, if necessary
	else:
		return ""


def Process008Date2(row):
	date1 = row[0]
	date2 = row[1]

	if date2 and date2 != "" and REGEX008DATE.search(date2):
		# fill out year with zeros, if necessary
		return str(REGEX008DATE.search(date2).group(1)).ljust(4, '0')

	m = REGEX008DATE.search(date1)
	if m and m.group(3):
		d1 = m.group(1)
		d2 = m.group(3)
		if len(d2) == 4: # 4 digit year
			return d2
		else: # make d2 a 4 digit year
			newdate = [c for c in reversed(d1)] # d1 is a 4 digit year
			d2rev = [c for c in reversed(d2)]
			for i in range(len(d2rev)):
				newdate[i] = d2rev[i]
			return "".join(reversed(newdate))
	return ""

def Process856(row):
	string = row[0]
	urlpath = "http://library.mseag.org/e-resources/mseag/"
	m = REGEX856URL.search(string)
	if m:
		resource = m.group(1)
		if resource.startswith("DigiData"): # already urlencoded
			return urlpath + resource
		else:
			try:
				resource = resource[resource.index("DigiData"):]
				return urlpath + urllib.quote(resource.replace('\\', '/'), "/()")
			except ValueError:
				return string
	return string


def Process700(row):
	formOfEntry = row[0]
	firstName = row[1]
	lastName = row[2] if row[2] is not None else ""
	fullerName = row[3]
	year = row[4]
	result = "$a"
	if formOfEntry == '0' and firstName and lastName:
		result += firstName + ' ' + lastName.strip('.') + '.'
	else:
		if firstName and len(firstName) > 0:
			result += lastName + ', ' + firstName
		else:
			result += lastName
	if year:
		result += "$d" + year
	if fullerName:
		result += "$q(%s)" % fullerName
	return result




if __name__ == "__main__":
	import doctest
	doctest.testmod()
