from Posting import PostingClass
from Query import QueryClass
import math

class RetrievalClass:

	def __init__(self, compressed, docMapping):
		self.compressed = compressed
		self.docMapping = docMapping
		self.N = len(self.docMapping)
		self.docLengths = [docMapping[docId]['docLength'] for docId in docMapping]
		self.avgDL = sum(self.docLengths) / len(self.docLengths)
	
	def getVectorSpaceScore(self, termFreq, docFreq, fiq):
		idf = math.log(self.N / docFreq)
		docTermWeight = (1 + math.log(termFreq)) * idf
		queryTermWeight = (1 + math.log(fiq)) * idf
		score = docTermWeight * queryTermWeight

		return score

	def getBM25Score(self, docId, termFreq, docFreq, fiq):
		k1, k2, b = 1.5, 500, 0.75
		K = k1 * ((1 - b) + (b * self.docLengths[docId] / self.avgDL))

		num = self.N - docFreq + 0.5
		den = docFreq + 0.5
		term1 = math.log(num / den)
		term2 = ((k1 + 1) * termFreq) / (K + termFreq)
		term3 = ((k2 + 1) * fiq) / (k2 + fiq)
		score = term1 * term2 * term3

		return score

	def termAtATimeRetrievalModels(self, queryTerms, invertedIndex, k, model):
		pQueue = {}
		fiq = {}
		for word in queryTerms:
			fiq[word] = queryTerms.count(word)
		queryTerms = list(dict.fromkeys(queryTerms))

		for word in queryTerms:
			posting = PostingClass(invertedIndex)
			postingList, termFreq, docFreq = posting.getPostingList(word)

			for docId in postingList:
				if docId not in pQueue:
					pQueue[docId] = 0
				if model == 'skadur-vspace':
					pQueue[docId] += self.getVectorSpaceScore(termFreq[docId], docFreq, fiq[word])
				if model == 'skadur-bm25':
					pQueue[docId] += self.getBM25Score(docId, termFreq[docId], docFreq, fiq[word])

		if model == 'skadur-vspace':
			for docId in self.docMapping:
				if docId in pQueue:
					pQueue[docId] = pQueue[docId] / self.docMapping[docId]['docLength']

		pQueue = sorted(pQueue.items(), key=lambda x:x[1], reverse=True)
		return pQueue[:k]

	def getJMScore(self, docId, termFreq):
		jm_lambda = 0.2

		collTerm = jm_lambda * sum(termFreq.values()) / sum(self.docLengths)
		if docId in termFreq:
			collTerm += (1 - jm_lambda) * termFreq[docId] / self.docLengths[docId]
		score = math.log(collTerm)

		return score

	def getDirichletScore(self, docId, termFreq):
		mu = 1200
		tf = 0
		if docId in termFreq:
			tf = termFreq[docId]
		collTerm = mu * sum(termFreq.values()) / sum(self.docLengths)
		score = math.log((tf + collTerm) / (self.docLengths[docId] + mu))

		return score

	def documentAtATime(self, queryTerms, invertedIndex, k, model):
		queryInvertedIndex = {}
		pQueue = {}

		for word in queryTerms:
			posting = PostingClass(invertedIndex)
			postingList, termFreq, docFreq = posting.getPostingList(word)
			queryInvertedIndex[word] = {'postingList': postingList, 'tf': termFreq, 'df': docFreq}

		for docId in self.docMapping:
			score = 0
			for word in queryTerms:
				# if docId in queryInvertedIndex[word]:
				# 	if model == '':
				# 		pQueue[docId] += len(queryInvertedIndex[word][docId])
				if model == 'skadur-lm-jm':
					score = self.getJMScore(docId, queryInvertedIndex[word]['tf'])
				if model == 'skadur-lm-dirich':
					score = self.getDirichletScore(docId, queryInvertedIndex[word]['tf'])
				if docId not in pQueue:
					pQueue[docId] = 0
				pQueue[docId] += score

		pQueue = sorted(pQueue.items(), key=lambda x:x[1], reverse=True)
		return pQueue[:k]

	def runRetrieval(self, judgements):
		k = 10
		queryFiles = ["../data/queries.txt"]
		uniqueScenes = []
		for file in queryFiles:
			with open(file, "r") as f:
				content = f.read()
				if content[-1] == " " or content[-1] == "\n":
					content = content[:-1]
				lines = content.split("\n")

			for line in lines:
				if line[-1] == " ":
					line = line[:-1]
				words = line.split(" ")
				topic = words[0][:-1]
				words = words[1:]
				query = QueryClass(self.compressed)
				invertedIndex = query.invertedIndex

				# result = self.documentAtATime(words, invertedIndex, 10)
				rank = 0
				modelList = ['skadur-vspace', 'skadur-bm25', 'skadur-lm-jm', 'skadur-lm-dirich']
				outputList = ['../data/vs.trecrun', '../data/bm25.trecrun', '../data/ql-jm.trecrun', '../data/ql-dir.trecrun']
				for model in range(len(modelList)):
					f = open(outputList[model], 'a+')
					rank = 0
					if "lm" not in modelList[model]:
						result = self.termAtATimeRetrievalModels(words, invertedIndex, k, modelList[model])
					else:
						result = self.documentAtATime(words, invertedIndex, k, modelList[model])
					for pair in result:
						rank += 1
						f.write(topic + "\tskip\t" + self.docMapping[pair[0]]['sceneId'] + "\t" + str(rank) + "\t" + str(pair[1]) + "\t" + modelList[model] + "\n")
						if "vspace" not in modelList[model]:
							uniqueScenes.append(self.docMapping[pair[0]]['sceneId'])
					f.close()

		if judgements:
			with open('../data/judgements.txt', 'w+') as f:
				uniqueScenes = list(dict.fromkeys(uniqueScenes))
				for scene in uniqueScenes:
					f.write(scene + "\n")