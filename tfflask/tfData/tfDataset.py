import sys, os

class Lexeme:
	def __init__(self,id,total,gloss,beta,lex,plain,pos,lang):
		self.id = id if id else 0
		self.total = total if total else 0
		self.gloss = gloss
		self.beta = beta if beta else ''
		self.lex = lex
		self.plain = plain if plain else lex
		self.pos = pos
		self.lang = lang

from tf.app import use
from ..env import debug,mylog
class TfDataset:
	def getAPI(self):
		return self.api
	def getBooksDict(self):
		return self.booksDict
	def __init__(self,datasetPathname,version=None):
		self.dataset=use(datasetPathname,version) if version else use(datasetPathname)
		self.api=self.dataset.api
		self.posDict=None
		self.posGroups=None
		self.bookDict=None
		self.dbname='lxx'
	def getLexCount(self):
		return 0
	
	def isProperNoun(self, wordid):
		return (self.api.F.sp.v(wordid) == 'noun') and self.api.F.lex_utf8.v(wordid)[0].isupper()

	def getLex(self,wordid):
		return self.api.F.lex_utf8.v(wordid)
	
		# returns dict of lexemes and frequencies:
	def getLexemes(self,sections=[], restrict=[],exclude=[], min=1, gloss=False, totalCount=True,pos=False,checkProper=True, beta=True,type='all',common=False,plain=False):
		#mylog("Min: " + str(min))
		
		lexemes = {}
		sectionsLexemes = {}

		totalInstances = 0
		totalLexemes = 0
		totalWordsInSections = 0

		restrictStrings=[v['desc'] for (k,v) in theDicts['dict'].items() if k in restrict]
		excludeStrings=[v['desc'] for (k,v) in theDicts['dict'].items() if k in exclude]
		#print("restrictStrings: " + str(restrictStrings))
		restricted = True if len(restrictStrings) > 0 else False
		excluded  = True if len(excludeStrings) > 0 else False
		
		def includeWord(wordid):
			wordid=int(wordid)
			include = False
			nonlocal beta
			nonlocal checkProper
			nonlocal excludeStrings
			nonlocal excluded
			nonlocal gloss
			nonlocal pos
			nonlocal plain
			nonlocal restrictStrings
			nonlocal restricted
			nonlocal totalCount
			nonlocal totalInstances
			nonlocal totalLexemes
			nonlocal totalWordsInSections


			if (self.api.F.otype.v(wordid) == 'word'):
				#beta = F.lex.v(wordid)
				totalWordsInSections += 1
				#greek = F.lex_utf8.v(wordid)
				
				if (checkProper and self.isProperNoun(wordid)):
					# we have a name, and must account for that fact:
					if ((not excluded or 26 not in exclude) 
						and (not restricted or 26 in restrict)): #we should include it
						include = True
				else:# don't need to worry about names
					thePos = self.api.F.sp.v(wordid)
					if ( (not excluded or thePos not in excludeStrings)  
						and (not restricted or thePos in restrictStrings)):
						include = True
			
			return include
			

		def addLexes(nodeid,recursive=False):
			def addLex(wordid):
				nonlocal totalInstances
				nonlocal totalLexemes
				nonlocal totalWordsInSections
				nonlocal beta
				nonlocal plain
				nonlocal gloss
				nonlocal totalCount
				nonlocal pos

				if(includeWord(wordid)):	
					
					totalInstances += 1
					if (not self.getLex(wordid) in lexemes.keys()):
						totalLexemes +=1
						lexemes[self.getLex(wordid)] = {'count': 1, 'id': wordid}
						# track which of the give sections this word is in:
						if (common):
							sectionsLexemes[self.getLex(wordid)]=set([int(s) for s in (set(L.u(wordid)) & set(sections))])

						if (totalCount):
							lexemes[self.getLex(wordid)]['total'] = int(self.api.F.freq_lemma.v(wordid));
						if (gloss):
							lexemes[self.getLex(wordid)]['gloss'] = self.api.F.gloss.v(wordid)
						if (beta):
							lexemes[self.getLex(wordid)]['beta'] = self.api.F.lex.v(wordid)
						if (pos):
							lexemes[self.getLex(wordid)]['pos'] = self.api.F.sp.v(wordid)
							#print("Got pos!")
							if (lexemes[self.getLex(wordid)]['pos'] == 'noun' and self.getLex(wordid)[0].isupper()):
								if (checkProper):
									lexemes[self.getLex(wordid)]['pos'] = 'proper noun or name'
								else:
									lexemes[self.getLex(wordid)]['proper'] = True
					else:
						lexemes[self.getLex(wordid)]['count'] += 1
						if (common):
							sectionsLexemes[self.getLex(wordid)].update([int(s) for s in (set(self.api.L.u(wordid)) & set(sections))])
			
			id=int(nodeid)
			if (self.api.L.d(id) and not recursive):
				for w in self.api.L.d(id):
					addLexes(w,recursive=True)
			elif(self.api.F.otype.v(id) == 'word'):
				addLex(id)
			
		#print("sections: " + str(sections))
		if(len(sections) > 0):
			for s in sections:
				s=int(s)
				foundSuper = False
				for supersect in self.api.L.u(s):
					if ((str(supersect) in sections) or (supersect in sections)):
						foundSuper = True
				if(not foundSuper):
					addLexes(s)
		else:
			for o in self.api.N.walk():
				addLexes(o)
		#print(lexemes)		
		# sort lexemes?
		# 
		# 	
		theResponseObj = {
			'totalInstances': totalInstances,#i.e., number of words in this section
			'totalLexemes': totalLexemes,
			'totalWords':totalWordsInSections,
			'lexemes': lexemes if min == 1 else {k:v for (k,v) in lexemes.items() if int(v['count']) >= int(min)}
		}
		
		if (common):
			commonLexes = [g for (g,ss) in sectionsLexemes.items() if set(sections) <= ss]
			#print("commonlexes length: " + str(len(commonLexes)))
		#	print("set repon.common to: "+str(len(theResponseObj['common'])))
			theResponseObj['common']=commonLexes
		return  theResponseObj
		
	def getChaptersDict(self,book):
		#mylog("getChapters(" + str(book) + "," + db +")")
		return dict([(self.api.F.chapter.v(c), c) for c in self.api.L.d(book) if self.api.F.otype.v(c)=='chapter'])
		
	def getBooksDict(self):
		return dict([(b, self.api.F.book.v(b)) for b in self.api.N.walk() if self.api.F.otype.v(b) == 'book'])

### pasted from init.py:
	def getVersesFromNodeRange(self,startNode,endNode,showVerses=False):
		text = ''
		print("getVersesFromNodeRange(" +str(startNode) + ","+str(endNode)+")")
		
		if (startNode == endNode):
			text += self.api.T.text(startNode)
			print("	got single node; text= " + text)
		elif (startNode > 0 and endNode >= startNode):
			for i in range(startNode,endNode+1,1):
				if(self.api.F.otype.v(i) =='verse'):
					if(showVerses):
						sec=api.T.sectionFromNode(i)
						if (sec[2]):
							text+= str(sec[2]) +'. '
					text += self.api.T.text(i)
				else:
					print("Node " + str(i) + " was not a verse, but is: " + self.api.F.otype.v(i) +", text = " + self.api.T.text(i))
			print("	got range. text = " + text)

		return text.strip()
	
	# returns refs as {'refs': <string array>, 'nodes': <int array of verses>, 'bookCounts': <dict of booksids->count>, 'total', <total instances in BHS>}
	def getLexRefs(self,id,sections=[],detail=''):
		
		# optionally limits to instances within any of the selected sections, exluding all others:
		id=int(id)
		sections = [int(s) for s in sections] if sections.length else []
		mylog("getrefs: sections = [" + ",".join([str(s) for s in sections])+"]")
		if(self.api.F.otype.v(id) == 'word'):
			lex=self.lex(id)
			rNodes = {}
			bookCounts = {}
			queryDetail = 'verse'
			verseCounts={}
			if (detail):
				if (detail == "book"):
					queryDetail = 'book'
				elif (detail == "chapter"):
					queryDetail = 'chapter'

			#refs = {}
			for n in self.api.N.walk():
				if (self.api.F.otype.v(n) == 'word' and self.lex(n) == lex and (len(sections) == 0 or (len(set(self.api.L.u(n)) & set(sections)) > 0) )):
					sectionTuple= self.api.T.sectionTuple(n)
					if (queryDetail == 'book'):
						sectionNode = sectionTuple[0]
					elif (queryDetail == 'chapter'):
						sectionNode = sectionTuple[1]
					else:
						sectionNode = sectionTuple[2]

					#rNodes.add(sectionNode) # gets node of containing verse
					refTuple = self.api.T.sectionFromNode(n) # gets tuple of containing verse
					if (queryDetail == 'book'):
						refString = refTuple[0]
					elif (queryDetail == 'chapter'):
						refString = refTuple[0] + " " + str(refTuple[1])
					else:
						refString = refTuple[0] + " " + ":".join(map(str,refTuple[1:]))
					#refs.add(refString)
					bookid=api.L.u(n)[-1]
					if bookid not in bookCounts:
						bookCounts[bookid]=1
					else:
						bookCounts[bookid] +=1
					if sectionNode not in rNodes:
						rNodes[sectionNode]=refString
						verseCounts[sectionNode]=1
					else:
						verseCounts[sectionNode] +=1
						#rNodes[sectionNode]=refString+"(" + str(verseCounts[sectionNode]) + ")"

			return {'refs': list(rNodes.values()), 'nodes': list(rNodes.keys()), 'bookcounts': dict(bookCounts), 'total': sum(bookCounts.values())}
		else:
			return ''

	def getText(self,nodeId):
		
		try:
			return self.api.T.text(int(nodeId)).strip()
		except:
			return ''

	def getRef(self,nodeId):
		try:
			return " ".join(map(str, self.api.T.sectionFromNode(int(nodeId))))
		except:
			return ''


	def getNodeFromBcV(self,book,chapter,verse):
		node = 0
		
		print("calling nodeFromSection(" + book + "," + str(chapter) +"," + str(verse)+")")
		
		node=self.api.T.nodeFromSection((book,int(chapter),int(verse)))
		if (type(node) != int):
			node = 0
		print("...got node" + str(node))
		return node



	def sectionFromNode(self,node):
		
		section= self.api.T.sectionFromNode(node)
		string = ''
		if (len(section) == 3):
			string = str(section[0]) + " " + str(section[1]) + ":" + str(section[2])
		elif (len(section) == 2):
			string = str(section[0]) + " " + str(section[1])
		else:#book only:
			string = str(section[0])
		return string
	
	## static class function!
	def consolidateBibleRefs(strings):
		outString = ''
		if(len(strings) > 1):
			bookHash = {}
			for s in strings:
				if (" " in s):
					(book,chapV) = s.split(" ")
					if (book not in bookHash.keys()):
						bookHash[book] = {}#indexed by chaps
					if (":" in chapV):
						(chap, verse) = chapV.split(":")
						if (chap not in bookHash[book].keys()):
							bookHash[book][chap] = [verse]
						else:
							bookHash[book][chap].append(verse)
					else: # no verse given
						if (chapV not in bookHash[book].keys()):
							bookHash[book][chapV] = []
						#else: #chap exists, but no need to add since we don't have a verse
				else: #book only
					if (s not in bookHash.keys()):
						bookHash[s]={}

			#mylog(bookHash)
			
			for (b,cvs) in bookHash.items():
				outString = b + " " if not outString else outString + "; " + b
				cvss = ''
				for (c, vs) in cvs.items():
					if (cvss):
						cvss += "; " + c 
					else:
						cvss += " " + c

					vss = ",".join(vs)
					if (vss):
						cvss += ":" + vss
					
				outString += cvss
				
		else:
			outString = strings[0]
		
		return outString


