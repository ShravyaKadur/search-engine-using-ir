from Compressor import CompressorClass
from Retrieval import RetrievalClass
from Query import QueryClass
import json
import sys
import re

class IndexerClass:

	def __init__(self):
		self.collection = sys.argv[1]
		self.compressed = int(sys.argv[2])

	def createIndex(self):
		with open(self.collection) as f:
			content = json.loads(f.read())

		self.docMapping = {}
		self.invertedIndex = {}

		for scene in content["corpus"]:
			docId = scene["sceneNum"]
			text = scene["text"]
			# Split by white space
			words = re.split("\s+", text)
			docWords = {}
			# Creating mapping between docId and scene, play and document length
			self.docMapping[docId] = {'sceneId': scene["sceneId"], 'playId': scene["playId"], 'docLength': len(words)}

			for i in range(len(words)):
				word = words[i]
				if word:
					if word not in self.invertedIndex:
						self.invertedIndex[word] = [docId, 0]
					if word not in docWords:
						if self.invertedIndex[word][1] > 0:
							self.invertedIndex[word].extend([docId, 0])
						docWords[word] = len(self.invertedIndex[word]) - 1
					countIndex = docWords[word]
					self.invertedIndex[word][countIndex] += 1
					self.invertedIndex[word].append(i+1)
					
		return self.invertedIndex

	def writeMappings(self):
		with open('../data/docMapping.txt', 'w+') as f:
			f.write(str(self.docMapping))

	def writeIndex(self, invertedIndex):
		offset = 0
		lookup = dict()

		# Different destinations based on compression preference
		if self.compressed:
			indexFile = "compressedIndex"
			lookupFile = "compressedLookupTable"
		else:
			indexFile = "uncompressedIndex"
			lookupFile = "uncompressedLookupTable"

		with open("../data/" + indexFile, "wb+") as f:
			for k,v in invertedIndex.items():
				f.seek(offset, 0)
				for b in v:
					f.write(b.to_bytes(4, byteorder=sys.byteorder))
				lookup[k] = {'offset': offset, 'size': f.tell()-offset}
				offset = f.tell()

		with open("../data/" + lookupFile + ".txt", "w+") as f:
			f.write(str(lookup))


	def indexBuilder(self):
		self.createIndex()
		self.writeMappings()
		if self.compressed:
			compressor = CompressorClass()
			dInvertedIndex = compressor.deltaEncode(self.invertedIndex)
			vByteIndex = compressor.vByteCompression(dInvertedIndex)
			self.writeIndex(vByteIndex)
		else:
			self.writeIndex(self.invertedIndex)
		

def main():
	# Indexing and writing to files based on compression preference
	indexer = IndexerClass()
	# indexer.indexBuilder()

	# Running 7-word and 14-word queries; Also answering some collection questions
	query = QueryClass(indexer.compressed)
	# query.runQuery()
	docMapping = query.readMappings()

	# Running the timed task
	retrieval = RetrievalClass(indexer.compressed, docMapping)
	retrieval.runRetrieval(False)

if __name__=="__main__":
	main()