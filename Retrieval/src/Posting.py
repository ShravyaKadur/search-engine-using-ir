class PostingClass:
	def __init__(self, invertedIndex):
		self.invertedIndex = invertedIndex
		self.postingList = {}
		self.termFreq = {}
		self.docFreq = 0

	def getPostingList(self, word):
		array = self.invertedIndex[word]
		i = 0

		while i < len(array):
			docId = array[i]
			size = int(array[i+1])
			positions = array[i+2:i+2+size]
			self.postingList[docId] = positions
			self.termFreq[docId] = size
			self.docFreq += 1
			i += size + 2

		return self.postingList, self.termFreq, self.docFreq