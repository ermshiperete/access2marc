# define custom functions here for use in processing SQL output

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
