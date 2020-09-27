class CompressorClass:

	def arrayToPosting(self, array):
		postingList = {}
		i = 0
		while i < len(array):
			docId = array[i]
			size = int(array[i+1])
			positions = array[i+2:i+2+size]
			postingList[docId] = positions
			i += size + 2

		return postingList

	def deltaEncode(self, invertedIndex):
		dInvertedIndex = {}
		for word in invertedIndex:
			postingList = self.arrayToPosting(invertedIndex[word])
			dInvertedIndex[word] = []
			prevDocId = 0

			for docId in postingList:
				deltaDocId = docId - prevDocId
				dInvertedIndex[word].extend([deltaDocId, len(postingList[docId])])
				dInvertedIndex[word].extend(postingList[docId])
				prevDocId = docId
		
		return dInvertedIndex

	def deltaDecode(self, dInvertedIndex):
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

	def vByteTermCompression(self, termPositionDic):
		b = []
		for v in termPositionDic:
			while v >= 128:
				b.append(v & 0x7f)
				v >>= 7
			b.append(v | 0x80)
		return b

	def vByteTermDecompression(self, array):
		new_array = []

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

	def vByteCompression(self, dInvertedIndex):
		vByteIndex = {}
		for word in dInvertedIndex:
			vByteIndex[word] = self.vByteTermCompression(dInvertedIndex[word])
		
		return vByteIndex

	def vByteDecompression(self, vByteIndex):
		dInvertedIndex = {}
		for word in vByteIndex:
			dInvertedIndex[word] = self.vByteTermDecompression(vByteIndex[word])

		return dInvertedIndex
