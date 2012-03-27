class Logger(object):

	def __init__(self, stream, verbose, label = ''):
		self.stream = stream
		self.verbose = verbose
		self.label = label

	def Debug(self, msg, newline = True):
		if self.verbose:
			try:
				if len(self.label) > 0 and newline and len(str(msg).strip()) > 0:
					self.stream.write('\n' + self.label + ': ')
				self._log(msg, newline)
			except UnicodeEncodeError:
				pass

	def Log(self, msg, newline = True):
		self._log(msg, newline)

	def _log(self, msg, newline):
		self.stream.write(str(msg))
		if newline:
			self.stream.write('\n')
