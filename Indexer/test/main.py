import json
import re
import sys

def createIndex():
	with open('data/shakespeare-scenes.json') as f:
		content = json.loads(f.read())

	sceneMapping = []
	playMapping = []
	wordStats = {}

	invertedIndex = {}

	for scene in content["corpus"]:
		docId = scene["sceneNum"]
		sceneMapping.append([docId, scene["sceneId"]])
		playMapping.append([docId, scene["playId"]])

		text = scene["text"]
		words = re.split("\s+", text)
		docWords = {}
		for i in range(len(words)):
			word = words[i]
			if word:
				if word not in invertedIndex:
					invertedIndex[word] = [docId, 0]
					wordStats[word] = {'termFreq': 0, 'docFreq': 0}
				if word not in docWords:
					if invertedIndex[word][1] > 0:
						invertedIndex[word].extend([docId, 0])
					docWords[word] = len(invertedIndex[word]) - 1
					wordStats[word]['docFreq'] += 1
				countIndex = docWords[word]
				invertedIndex[word][countIndex] += 1
				invertedIndex[word].append(i+1)
				wordStats[word]['termFreq'] += 1
				
	return invertedIndex, wordStats, sceneMapping, playMapping

def writeMappings(sceneMapping, playMapping):
	with open('data/sceneMapping.txt', 'w+') as f:
		for mapping in sceneMapping:
			f.write(str(mapping[0]) + " " + str(mapping[1]) + "\n")

	with open('data/playMapping.txt', 'w+') as f:
		for mapping in playMapping:
			f.write(str(mapping[0]) + " " + str(mapping[1]) + "\n")

def writeWordStats(wordStats):
	with open('data/wordStats.txt', 'w+') as f:
		f.write(str(wordStats))

def writeIndex(compressed, invertedIndex):
	offset = 0
	lookup = dict()

	if compressed:
		indexFile = "compressedIndex"
		lookupFile = "compressedLookupTable"
		with open("data/" + indexFile, "wb+") as f:
			for k,v in invertedIndex.items():
				f.seek(offset, 0)
				for b in v:
					f.write(b.to_bytes(4, byteorder=sys.byteorder))
				lookup[k] = {'offset': offset, 'size': f.tell()-offset}
				offset = f.tell()
	else:
		indexFile = "uncompressedIndex"
		lookupFile = "uncompressedLookupTable"
		with open("data/" + indexFile, "wb+") as f:
			for k,v in invertedIndex.items():
				f.seek(offset, 0)
				for b in v:
					# b_bytearray = str(b).encode()
					# b_int = int.from_bytes(b_bytearray, byteorder=sys.byteorder)
					# b_write = b_int.to_bytes(4, byteorder=sys.byteorder)
					f.write(b.to_bytes(4, byteorder=sys.byteorder))
				lookup[k] = {'offset': offset, 'size': f.tell()-offset}
				offset = f.tell()

	with open("data/" + lookupFile + ".txt", "w+") as f:
		f.write(str(lookup))

def readIndex(word, lookup):
	# print(lookup['scene'])
	offset = lookup[word]['offset']
	size = lookup[word]['size']
	array = []
	with open("data/uncompressedIndex", "rb") as f:
		f.seek(offset)
		m = f.read(size)
		while len(m) > 0:
			character = m[:4]
			array.append(int.from_bytes(character, byteorder=sys.byteorder))
			m = m[4:]
	
	return array

def getLookup():
	with open("data/lookupTable.txt", "r") as f:
		lookup = eval(f.read())

	return lookup

def arrayToPosting(array):
	postingList = {}
	i = 0
	while i < len(array):
		docId = array[i]
		size = int(array[i+1])
		positions = array[i+2:i+2+size]
		postingList[docId] = positions
		i += size + 2

	return postingList

def deltaEncode(invertedIndex):
	dInvertedIndex = {}
	for word in invertedIndex:
		postingList = arrayToPosting(invertedIndex[word])
		dInvertedIndex[word] = []
		prevDocId = 0

		for docId in postingList:
			deltaDocId = docId - prevDocId
			dInvertedIndex[word].extend([deltaDocId, len(postingList[docId])])
			dInvertedIndex[word].extend(postingList[docId])
			prevDocId = docId
	
	return dInvertedIndex

def deltaDecode(dInvertedIndex):
	invertedIndex = {}
	for word in dInvertedIndex:
		invertedIndex[word] = []
		prevDocId = 0
		array = dInvertedIndex[word]
		i = 0

		while i < len(array):
			deltaDocId = array[i]
			size = int(array[i+1])
			positions = array[i+2:i+2+size]
			docId = deltaDocId + prevDocId
			invertedIndex[word].extend([docId, size])
			invertedIndex[word].extend(positions)
			prevDocId += deltaDocId
			i += size + 2

	return invertedIndex

def vByteTermCompression(termPositionDic):
	b = []
	for v in termPositionDic:
		while v >= 128:
			b.append(v & 0x7f)
			v >>= 7
		b.append(v | 0x80)
	return b

def vByteTermDecompression(array):
	new_array = []
	# for number in array:
	# 	mynumber = ''
	# 	full_binary_number = (bin(number)[2:].zfill(24))
	# 	full_binary_number_string = str(full_binary_number)
	# 	for i in range(1, 8):
	# 		mynumber += full_binary_number_string[i]
	# 	for i in range(9, 16):
	# 		mynumber += full_binary_number_string[i]
	# 	for i in range(17, 24):
	# 		mynumber += full_binary_number_string[i]
	# 	my_binary_number = int(mynumber, base=2)
	# 	new_array.append(my_binary_number)

	i = 0
	while i < len(array):
		pos = 0
		result = (int)(array[i] & 0x7f)
		while (int)(array[i] & 0x80) == 0:
			i += 1
			pos += 1
			b = (int)(array[i] & 0x7f)
			result |= (b << (7*pos))
		new_array.append(result)
		i += 1

	return new_array

def vByteCompression(dInvertedIndex):
	vByteIndex = {}
	for word in dInvertedIndex:
		vByteIndex[word] = vByteTermCompression(dInvertedIndex[word])
	
	return vByteIndex

def vByteDecompression(vByteIndex):
	dInvertedIndex = {}
	for word in vByteIndex:
		dInvertedIndex[word] = vByteTermDecompression(vByteIndex[word])

	return dInvertedIndex

def compressIndex(invertedIndex):
	dInvertedIndex = deltaEncode(invertedIndex)
	vByteIndex = vByteCompression(dInvertedIndex)
	writeIndex(True, vByteIndex)
	# print(len(invertedIndex["hubert"]), len(vByteIndex["hubert"]))

def readCompressedIndex():
	with open("data/compressedLookupTable.txt", "r") as f:
		lookup = eval(f.read())

	vByteIndex = {}
	for word in lookup:
		offset = lookup[word]['offset']
		size = lookup[word]['size']
		array = []
		with open("data/compressedIndex", "rb") as f:
			f.seek(offset)
			m = f.read(size)
			while len(m) > 0:
				character = m[:4]
				array.append(int.from_bytes(character, byteorder=sys.byteorder))
				m = m[4:]
		vByteIndex[word] = array

	dInvertedIndex = vByteDecompression(vByteIndex)
	invertedIndex = deltaDecode(dInvertedIndex)

	return invertedIndex


# invertedIndex, wordStats, sceneMapping, playMapping = createIndex()
# dInvertedIndex = deltaEncode(invertedIndex)
# comp = vByteTermCompression(dInvertedIndex["hubert"])
# print(comp)
# print(vByteTermDecompression(comp))

# compressIndex(invertedIndex)
retreivedIndex = readCompressedIndex()
print(retreivedIndex)

# writeIndex(invertedIndex)
# writeWordStats(wordStats)
# readIndex('hubert')
# readIndex()


# print(invertedIndex)
