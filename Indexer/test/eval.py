import main
import random

invertedIndex = {}

def getInvertedIndex(word, lookup):
	if word not in invertedIndex:
		array = main.readIndex(word, lookup)
		invertedIndex[word] = array

	return invertedIndex[word]

def getWords():
	with open("data/lookupTable.txt", "r") as f:
		lookup = eval(f.read())
	words = list(lookup.keys())

	return words, lookup

def generate7Query():
	words = getWords()
	with open("data/groupsOf7.txt", "w+") as f:
		for i in range(100):
			for j in range(7):
				randIndex = random.randrange(len(words))
				f.write(words[randIndex] + " ")
			f.write("\n")

def getPosting(word, lookup):
	array = getInvertedIndex(word, lookup)
	postingList = {}
	termFreq = 0
	docFreq = 0
	i = 0
	while i < len(array):
		docId = array[i]
		size = int(array[i+1])
		positions = array[i+2:i+2+size]
		postingList[docId] = positions
		termFreq += size
		docFreq += 1
		i += size + 2

	# print(postingList)
	return postingList, termFreq, docFreq

def getAdjacentCount(positionsA, positionsB):
	count = 0
	for pos in positionsA:
		if pos+1 in positionsB:
			count += 1
			# return 1

	return count

def calculateDice(wordA, wordB, lookup):
	postingA, termFreqA, docFreqA = getPosting(wordA, lookup)
	postingB, termFreqB, docFreqB = getPosting(wordB, lookup)
	nAB = 0

	for docIdA in postingA.keys():
		for docIdB in postingB.keys():
			if docIdA == docIdB:
				nAB += getAdjacentCount(postingA[docIdA], postingB[docIdB])
	print(nAB, termFreqA, termFreqB)
	diceCofficient = nAB / (termFreqA + termFreqB)

	return diceCofficient


def getDicePair(word):
	diceWord = ""
	words, lookup = getWords()
	maxDice = -1

	for wordB in words:
		diceCofficient = calculateDice(word, wordB, lookup)
		# print(wordB, diceCofficient)
		if diceCofficient > maxDice:
			maxDice = diceCofficient
			diceWord = wordB

	return diceWord

def generate14Query():
	with open("data/groupsOf7.txt", "r") as f:
		content = f.read()
		content = content[:-1]

	with open("data/groupsOf14.txt", "w+") as f:
		groups = content.split("\n")
		for group in groups:
			group = group[:-1]
			wordsFrom7 = group.split(" ")
			for word in wordsFrom7:
				diceWord = getDicePair(word)
				# print(len(invertedIndex))
				f.write(word + " " + diceWord + " ")
			f.write("\n")



# generate7Query()
# generate14Query()
# words, lookup = getWords()
# print(calculateDice("that", "is", lookup))
# print(getDicePair("threatening"))


# words, lookup = getWords()
# print(getPosting("this", lookup))
# print("*********")
# print(getPosting("is", lookup))
