from Compressor import CompressorClass
from Posting import PostingClass
from os import path
import random
import sys

class QueryClass:

	def __init__(self, compressed):
		self.compressed = compressed
		self.invertedIndex = {}
		self.invertedIndex = self.getInvertedIndex()

	def getInvertedIndex(self):
		if not self.invertedIndex:
			if self.compressed:
				indexFile = "compressedIndex"
				lookupFile = "compressedLookupTable"
			else:
				indexFile = "uncompressedIndex"
				lookupFile = "uncompressedLookupTable"

			with open("../data/" + lookupFile + ".txt", "r") as f:
				lookup = eval(f.read())

			for word in lookup:
				offset = lookup[word]['offset']
				size = lookup[word]['size']
				array = []
				with open("../data/" + indexFile, "rb") as f:
					f.seek(offset)
					m = f.read(size)
					while len(m) > 0:
						character = m[:4]
						array.append(int.from_bytes(character, byteorder=sys.byteorder))
						m = m[4:]
				self.invertedIndex[word] = array

			if self.compressed:
				vByteIndex = self.invertedIndex
				compressor = CompressorClass()
				dInvertedIndex = compressor.vByteDecompression(vByteIndex)
				self.invertedIndex = compressor.deltaDecode(dInvertedIndex)
		self.words = list(self.invertedIndex.keys())

		return self.invertedIndex

	def generate7Query(self):
		if not path.exists("../data/7query.txt"):
			with open("../data/7query.txt", "w+") as f:
				for i in range(100):
					for j in range(7):
						randIndex = random.randrange(len(self.words))
						f.write(self.words[randIndex] + " ")
					f.write("\n")

	def getAdjacentCount(self, positionsA, positionsB):
		count = 0
		for pos in positionsA:
			if pos+1 in positionsB:
				count += 1

		return count

	def calculateDice(self, wordA, wordB):
		posting = PostingClass(self.invertedIndex)
		postingA, termFreqA, docFreqA = posting.getPostingList(wordA)
		postingB, termFreqB, docFreqB = posting.getPostingList(wordB)
		nAB = 0

		for docIdA in postingA.keys():
			for docIdB in postingB.keys():
				if docIdA == docIdB:
					nAB += self.getAdjacentCount(postingA[docIdA], postingB[docIdB])
		diceCofficient = nAB / (termFreqA + termFreqB)

		return diceCofficient

	def getDicePair(self, word):
		diceWord = ""
		maxDice = -1

		for wordB in self.words:
			diceCofficient = self.calculateDice(word, wordB)
			if diceCofficient > maxDice:
				maxDice = diceCofficient
				diceWord = wordB

		return diceWord

	def generate14Query(self):
		with open("../data/7query.txt", "r") as f:
			content = f.read()
			content = content[:-1]

		if not path.exists("../data/14query.txt"):
			with open("../data/14query.txt", "w+") as f:
				groups = content.split("\n")
				for group in groups:
					group = group[:-1]
					wordsFrom7 = group.split(" ")
					for word in wordsFrom7:
						diceWord = self.getDicePair(word)
						f.write(word + " " + diceWord + " ")
					f.write("\n")

	def computeFrequencies(self):
		self.frequencyList = {}
		for word in self.invertedIndex:
			_, termFreq, docFreq = self.getPostingList(word)
			self.frequencyList[word] = {'docFreq': docFreq, 'termFreq': termFreq}

		return self.frequencyList

	def readMappings(self):
		with open("../data/docMapping.txt", "r") as f:
			docMapping = eval(f.read())

		return docMapping

	def collectionQueries(self):
		playLengths = {}
		shortest = 100000
		avgLength = 0.0
		docMapping = self.readMappings()

		for doc in docMapping:
			docLength = docMapping[doc]['docLength']
			play = docMapping[doc]['playId']
			if play not in playLengths:
				playLengths[play] = 0
			playLengths[play] += docLength
			if docLength < shortest:
				shortestDoc = doc
				shortest = docLength
			avgLength += docLength
		avgLength /= len(docMapping)
		play_max = max(playLengths.keys(), key=(lambda k: playLengths[k]))
		play_min = min(playLengths.keys(), key=(lambda k: playLengths[k]))

		print("Average scene length = " + str(avgLength))
		print("Shortest scene = " + docMapping[shortestDoc]["sceneId"] + "\t Length = " + str(shortest))
		print("Longest play = " + play_max + "\t Length = " + str(playLengths[play_max]))
		print("Shortest play = " + play_min + "\t Length = " + str(playLengths[play_min]))

		return avgLength


	def runQuery(self):
		self.generate7Query()
		self.generate14Query()
		self.collectionQueries()