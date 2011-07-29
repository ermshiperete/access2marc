# define custom functions here for use in processing SQL output

import re

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

def MainEntryPersonalName_a(row):
	firstname = row[0].strip(",.")
	lastname = row[1].strip(",.")
	result = ""
	if lastname:
		result += lastname
	if firstname:
		result += ", " + firstname + "."
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
	if title.find(':') > -1:
		if statement is not None and statement != '':
			return title[title.index(':')+1:] + ' /' # slash for statement of resp.
		else:
			return title[title.index(':')+1:]
	else:
		return None

def Process008Date1(row):
	date = row[0]
	p = re.compile(r'(c)?(\d+)[\s\.-]*(\d+)?')
	m = p.search(date)
	if m:
		mode = 'normal'
		if m.group(1) == 'c':
			mode = 'addzeros'
		return _fixDate(m.group(2), mode)
	else:
		return ""



def _fixDate(digits, mode='normal'):
	if not digits:
		return ""

	if mode == 'addzeros' :
		return str(digits).ljust(4, '0')
	elif int(digits) < 21:
		return "20%02d" % int(digits)
	elif int(digits) > 20 and int(digits) < 100:
		return "19%02d" % int(digits)
	elif int(digits) < 1000:
		return "%03d0" % int(digits)
	else:
		return str(digits)


	# examples of Date1 to process
	# 19
	# c1995
	# c1995-c2000
	# 2000-01
	# 2003
	# 05-07

def Process008Date2(row):
	date1 = row[0]
	date2 = row[1]
	p = re.compile(r'(\d+)[\s\.-]*(\d+)?')

	if date2 and date2 != "" and p.search(date2):
		return _fixDate(p.search(date2).group(1))

	if p.search(date1):
		return _fixDate(p.search(date1).group(2))

	return ""



if __name__ == "__main__":
	import doctest
	doctest.testmod()
