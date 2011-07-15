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
	print(row)
	result = ""
	if lastname:
		result += lastname
	if firstname:
		result += ", " + firstname + "."
	return result
