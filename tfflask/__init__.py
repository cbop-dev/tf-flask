import sys, os
#from tf.fabric import Fabric
from tf.app import use
from tf.advanced import sections

from flask import Flask, request, Response
from wordcloud import WordCloud, STOPWORDS
from pathlib import Path
from flask_cors import CORS
from .tfData.tfLXX import TfLXX
from .env import mylog, debug
#debug=False


def create_app():
#	print("LOADING APP!!!========================")
	posDict = TfLXX.posDict
	posGroups =TfLXX.posGroups
	tfLxxBooksDict=TfLXX.bookDict

	theBooksDict = tfLxxBooksDict

	enableNT=True
	enableBHS=False
	debug = False

	NT = None
	theDB = None

	if (enableBHS):
		from .tfData import tfBhs
		bhsPosGroups=tfBhs.bhsPosGroups
		bhsPosDict=tfBhs.bhsPosDict
		tfBhsBooksDict=tfBhs.tfBhsBooksDict
		BHS = use('etcbc/bhsa')
		bhsA = BHS.api
		theDB = BHS
		theBooksDict=tfBhsBooksDict

	if (enableNT):
		from .tfData import tfNT
		ntBooksDict = tfNT.ntBooksDict
		NT = use('CenterBLC/N1904')
		NTa = NT.api
		theDB = NT
		theBooksDict=ntBooksDict


	LXX = use("CenterBLC/LXX", version="1935", hoist=globals())

	app = Flask(__name__)

	app.config['SERVER_NAME'] = "localhost.localdomain:5000"
	CORS(app)


	@app.route("/<string:db>/lex/common/")
	@app.route("/lex/common/")
	def getCommonRoute(db='lxx'):
		return ''

	@app.route("/<string:db>/lex/<int:lexid>")
	@app.route("/lex/<int:lexid>")
	def getLexInfo(lexid,db='lxx'):
		api=getAPI(db)
		lexid=int(lexid)
		if (db == 'lxx'):
			if (lexid > 0 and api.F.otype.v(lexid) == 'word'):
				theLexObj = {'id': lexid}
				theLexObj['total'] = api.F.freq_lemma.v(lexid)
				theLexObj['gloss'] = api.F.gloss.v(lexid)
				
				theLexObj['beta']=api.F.lex.v(lexid)
				theLexObj['greek'] = api.F.lex_utf8.v(lexid)
				theLexObj['pos'] = api.F.sp.v(lexid) if theLexObj['greek'][0].islower() else 'proper noun or name'
				
				return theLexObj
		elif (enableBHS and  db == 'bhs'):
			#bhsF=BHS.api.F
			if (lexid > 0 and api.otype.v(lexid) == 'word'):
				theLexObj = {'id': lexid}
				theLexObj['total'] = api.freq_lex.v(lexid)
				theLexObj['gloss'] = api.gloss.v(lexid)
				theLexObj['beta']=api.lex0.v(lexid)
				theLexObj['hebrew'] = api.lex(lexid)
				theLexObj['hebrew_plain'] = api.lex_utf8.v(lexid)
				theLexObj['pos'] = api.sp.v(lexid)
				return theLexObj

		else:
			return ''


	@app.route("/bhs/test")
	def bhsTest():
		return "Hello BHS World!"

	@app.route("/<string:db>/lex/freq/<int:lexid>")
	@app.route("/lex/freq/<int:lexid>")
	def getLexCount(lexid, db='lxx'):
		
		if (db == 'lxx'):
			return LXX.api.Feature.freq_lemma.v(lexid)
		elif (enableBHS and db == 'bhs'):
			mylog("db == bhs...")
			count = str(bhsA.Feature.freq_lex.v(lexid))
			mylog("count: " + count)
			return count

	@app.route("/<string:db>/wordcloud")
	@app.route("/wordcloud")
	def wordCloudRoute(db='lxx'):
		
		theLexemesResp=lexemesRoute(db)
		theLexemes=theLexemesResp['lexemes']
		response = ''

		if (theLexemes.values()):
			filteredLexemes= {}
			if (not 'gloss' in list(theLexemes.values())[0].keys()):
				filteredLexemes = {k:int(v['count']) for (k,v) in theLexemes.items()}
				#print("Wait! no glosses??")
			else:
				#filteredLexemes = {v['gloss'].split(";")[0].strip():int(v['count'])
				#	for (k,v) in sorted(theLexemes.items(),key=lambda i:i[1]['count'],reverse=True) if not (v['gloss'].split(";")[0].strip() in filteredLexemes)}
				for (k,v) in sorted(theLexemes.items(),key=lambda i:i[1]['count'],reverse=True):
					engGloss=v['gloss'].split(";")[0].strip()
					if not (engGloss in filteredLexemes.keys()):
						filteredLexemes[engGloss]=v['count']

			
			#print({l:v for (l,v) in filteredLexemes.items() if 'lord' in l or 'God' in l})
			title=''
			if(request.args.get('invert')):
				for (k,v) in filteredLexemes.items():
					filteredLexemes[k]=-filteredLexemes[k]

			if (request.args.get('title') and request.args.get('sections') ):
			
				titles = []
				if(request.args.get('sections')):
					sections=request.args.get('sections').split(',')
					titles = titles + [str(sectionFromNode(int(s))) for s in sections if int(s) > 0]
			
				title = consolidateBibleRefs(titles)
			#	print("title: " + title)
			maxWords = request.args.get('maxWords')
			
			if(maxWords):
				response=Response(genWordCloudSVG(filteredLexemes,title=title,maxWords=int(maxWords)), mimetype='image/svg+xml')
			else:
				response=Response(genWordCloudSVG(filteredLexemes,title=title), mimetype='image/svg+xml')
		else:
			the404 = {":-(":15,"404":25, "try again!":10,"formless":3, "void": 2 }
			response=Response(genWordCloudSVG(the404), mimetype='image/svg+xml')
			
		return response

	@app.route("/<string:db>/lex")
	@app.route("/lex")
	def lexemesRoute(db='lxx'):
		theDicts=getDicts(db)
		checkProper =  True if request.args.get('proper') != 'false' else False
		#print("lex route: checkProper = " + str(checkProper))
		sections = []
		#if(request.args.get('sections') and len(request.args.get('sections') > 0 )):
		#	print("Have sections: " + request.args.get('sections'))
		#	sections = [int(s) for s in request.args.get('sections').split(',')]
		sections = [int(s) for s in request.args.get('sections').split(',')] if (request.args.get('sections')) else []
		restrictParamsList= request.args.get('restrict').split(',') if (request.args.get('restrict')) else []
		excludeParamsList= request.args.get('exclude').split(',') if (request.args.get('exclude')) else []
		pos = request.args.get('pos')
		beta = request.args.get('beta') if request.args.get('beta') else True
		plain = request.args.get('plain') if request.args.get('plain') else False
		common = True if request.args.get('common') else False
		#if (common):
	#		print("using common flag...")
		restrictedIds=set([int(x) for x in restrictParamsList if x.isdigit()])

		for (abbrev,iArray) in theDicts['groups'].items():
			if (abbrev in restrictParamsList):
				restrictedIds.update(theDicts['groups'][abbrev])
				#restrictedIds.remove(abbrev)
		mylog("restrictedIds: " + str(restrictedIds))

		excludedIds=set([int(x) for x in excludeParamsList if x.isdigit()])
		for (abbrev,iArray) in theDicts['groups'].items():
			if (abbrev in excludeParamsList):
				excludedIds.update(theDicts['groups'][abbrev])
		mylog("excludedIds: " + str(excludedIds))

		min = request.args.get('min') if ( request.args.get('min')) else 1
		gloss = True if ( request.args.get('gloss') and int(request.args.get('gloss')) != 0) else False
		#print("Gloss: " + str(gloss))
		#print("calling getLexemes with common = " + str(common))
		returnObject= getLexemes(sections=sections, restrict=list(restrictedIds), 
							exclude=list(excludedIds), min=min, gloss=gloss,pos=pos,checkProper=checkProper, beta=beta, common=common,db=db,plain=plain)
		#print("getLexemes about to return with common value of: [" + ",".join(returnObject['common']) + "]")
		return returnObject

	@app.route("/chapters/")
	@app.route("/<string:db>/chapters/")
	def allChaptersRoute(db='lxx'):
		api=getAPI(db)
		booksChaps={}
		#booksDict = tfLxxBooksDict
		
		if (enableBHS and db == 'bhs'):
			booksDict = tfBhsBooksDict
		
		for bid in theBooksDict.keys():
			booksChaps[bid]=getChaptersDict(bid, db)
		
		return booksChaps

	@app.route("/<string:db>/chapters/<int:book>")
	@app.route("/chapters/<int:book>")
	def chaptersRoute(book, db='lxx'):
		return getChaptersDict(book, db)

	@app.route("/<string:db>/books")
	@app.route("/books")
	def booksRoute(db='lxx'):
		return getBooksDict(db)

	@app.route("/<string:db>/getrefs/<int:id>")
	@app.route("/getrefs/<int:id>")
	def getrefsRoute(id, db='lxx'):
		return getLexRefs(id, db)

	@app.route("/<string:db>/words/<int:id>")
	@app.route("/words/<int:id>")
	def getWords(id,db='lxx'):
		api=getAPI(db)
		if (not request.args.get('features')):
			try:
				words = [{'id': w, 'text': getText(w,db),'lemma': api.lex(w)} for w in api.L.d(id) if api.F.otype.v(w) == 'word']
			except:
				words = []
		else:
	#		features = ['sp','gn','tense','mood']
			words = [{'id': w, 'text': getText(w,db),'lemma': api.lex(w),
				'features': {'pos':api.F.sp.v(w)}} for w in api.L.d(id) if api.F.otype.v(w) == 'word']
			for w in words:
				if (api.F.sp.v(w['id']) == "verb"):
					w['features']['tense'] = api.F.tense.v(w['id'])
			
		return words

	@app.route("/<string:db>/text/<int:id>")
	@app.route("/text/<int:id>")
	def textRoute(id,db='lxx'):
		api=getAPI(db)
		return {'section': getRef(id,db), 'text': getText(id,db), 'id':int(id), 'type': api.F.otype.v(int(id))}

	@app.route("/texts/")
	@app.route("/<string:db>/texts/", methods=['GET','POST'])
	def textsRoute(db='lxx'):
		texts = []
		ids = []
		ids=request.args.get("sections").split(",")
		try:
			for id in ids:
				texts.append({'section':getRef(id,db), 'text':getText(id,db), 'id': int(id)})
		except:
			texts=[]
		return texts

	@app.route("/<string:db>/node")
	@app.route("/node")
	def getNodeFromRefRoute(db='lxx'):
		api=getAPI(db)
		node = 0
		book = request.args.get('book')	
		chapter = request.args.get('chapter')
		verse = request.args.get('verse')	
		if (book and len(book) > 0):
			ref = book + " " + chapter if chapter and len(chapter) > 0 else book
			ref += ":" + verse if chapter and len(chapter) > 0 and verse and len(verse) > 0 else ''
			if (db=='lxx'):
				theDB=LXX
			elif(db=='bhs'):
				theDB=BHS
			elif(db=='nt'):
				theDB=NT
			secs = sections.nodeFromSectionStr(theDB,ref)

			if ((type(secs) is int) and secs > 0):
				node = secs

		return str(node)

	@app.route("/<string:db>/verses")
	@app.route("/verses")
	def getVersesFromRange(db='lxx'):
		api=getAPI(db)
		book = request.args.get('book').strip()
		chapter = request.args.get('chapter').strip()
		showVerses = True
		if (request.args.get('showVerses') and request.args.get('showVerses')=='0'):
			showVerses = False
		if (len(chapter) > 0):
			chapter = int(chapter)

		startVerse = request.args.get('start').strip()
		if (len(startVerse) > 0):
			startVerse = int(startVerse)
		endVerse = request.args.get('end').strip()
		
		if (len(endVerse) > 0):
			endVerse = int(endVerse)

		verses = ''
		startNode = getNodeFromBcV(book,chapter,startVerse,db)
		endNode = getNodeFromBcV(book,chapter,endVerse,db)
		ref = ''
		if (startNode == 0  and endNode == 0):
			print("got nothing")
		else:
			if ((startNode == 0 or startNode == None) and (endNode != 0 and endNode != None)):
				mylog(f"got end node {endNode} but no start node! trying to fix...")
				for i in range(startVerse + 1,endVerse+1, 1):
					if (startNode == None):
						startNode = getNodeFromBcV(book,chapter,i,db)
			
			if ((endNode == 0 or endNode == None) and (startNode != None and startNode != 0)):
				mylog(f"got start node {startNode} but no end node! trying to fix with range:")
				for i in range(endVerse-1, startVerse-1, -1):
					if (endNode == 0 or endNode == None):
						endNode = getNodeFromBcV(book,chapter,i,db)
			if (startNode != None and endNode != None and startNode > 0 and endNode > 0 and endNode >= startNode):
				verses = getVersesFromNodeRange(startNode,endNode,showVerses,db)
				print("calling getVersesFromNodeRange("+str(startNode)+","+str(endNode)+")")
				start = api.T.sectionFromNode(startNode)
				if (startNode < endNode):
					ref = start[0] + " " + str(start[1]) +":"+str(start[2])+"-"+str(api.T.sectionFromNode(endNode)[-1])
				else:
					ref = start[0] + " " + str(start[1]) +":"+str(start[2])
			else:
				print("got no nodes from range!")
			
		return {'text': verses, 'reference': ref}
		
	@app.route("/<string:db>/verses/",methods=['POST'])
	def getVersesPost(db='lxx'):
		return request.form['chapters'] if request.form['chapters'] else 'nada'

	@app.route("/<string:db>/verse")
	@app.route("/verse")
	def getVerse(db='lxx'):
		api=getAPI(db)
		book = request.args.get('book').strip()
		chapter = int(request.args.get('chapter').strip())
		verse = int(request.args.get('verse').strip())
		ref = ''
		node = getNodeFromBcV(book,chapter,verse,db)
		print("getVerse url calling getNodeFromBcV("+ ",".join([book,str(chapter),str(verse)])+")")
		print("got node " + str(node))
		if ((type(int(node)) == int) and int(node) > 0):
			text = getText(node,db)
			print("Go text:'"+text+"' for node " + str(node))
			sec = api.T.sectionFromNode(node)
			ref = sec[0] + " "
			if (sec[1] > 0):
				ref += str(sec[1])
				if (sec[2] > 0):
					ref += ":" + str(sec[2])
		else:
			text = ''

		
		return {'text': text, 'reference': ref}
		
################################
# non-route functions:         #

	def getVersesFromNodeRange(startNode,endNode,showVerses=False,db='lxx'):
		text = ''
		print("getVersesFromNodeRange(" +str(startNode) + ","+str(endNode)+")")
		api=getAPI(db)
		if (startNode == endNode):
			text += api.T.text(startNode)
			print("	got single node; text= " + text)
		elif (startNode > 0 and endNode >= startNode):
			for i in range(startNode,endNode+1,1):
				if(api.F.otype.v(i) =='verse'):
					if(showVerses):
						sec=api.T.sectionFromNode(i)
						if (sec[2]):
							text+= str(sec[2]) +'. '
					text += api.T.text(i)
				else:
					print("Node " + str(i) + " was not a verse, but is: " + api.F.otype.v(i) +", text = " + api.T.text(i))
			print("	got range. text = " + text)

		return text.strip()
	
	# returns refs as {'refs': <string array>, 'nodes': <int array of verses>, 'bookCounts': <dict of booksids->count>, 'total', <total instances in BHS>}
	def getLexRefs(id,db='lxx'):
		api=getAPI(db)
		# optionally limits to instances within any of the selected sections, exluding all others:
		id=int(id)
		sections = [int(s) for s in request.args.get('sections').split(',')] if request.args.get('sections') else []
		mylog("getrefs: sections = [" + ",".join([str(s) for s in sections])+"]")
		if(api.F.otype.v(id) == 'word'):
			lex=api.lex(id)
			rNodes = {}
			bookCounts = {}
			queryDetail = 'verse'
			verseCounts={}
			if (request.args.get("detail")):
				if (request.args.get("detail") == "book"):
					queryDetail = 'book'
				elif (request.args.get("detail") == "chapter"):
					queryDetail = 'chapter'

			#refs = {}
			for n in api.N.walk():
				if (api.F.otype.v(n) == 'word' and api.lex(n) == lex and (len(sections) == 0 or (len(set(api.L.u(n)) & set(sections)) > 0) )):
					sectionTuple= api.T.sectionTuple(n)
					if (queryDetail == 'book'):
						sectionNode = sectionTuple[0]
					elif (queryDetail == 'chapter'):
						sectionNode = sectionTuple[1]
					else:
						sectionNode = sectionTuple[2]

					#rNodes.add(sectionNode) # gets node of containing verse
					refTuple = api.T.sectionFromNode(n) # gets tuple of containing verse
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

	def getText(nodeId,db='lxx'):
		api=getAPI(db)
		try:
			return api.T.text(int(nodeId)).strip()
		except:
			return ''

	def getRef(nodeId, db='lxx'):
		api=getAPI(db)
		try:
			return " ".join(map(str, api.T.sectionFromNode(int(nodeId))))
		except:
			return ''


	def getNodeFromBcV(book,chapter,verse,db='lxx'):
		node = 0
		api=getAPI(db)
		print("calling nodeFromSection(" + book + "," + str(chapter) +"," + str(verse)+")")
		
		node=api.T.nodeFromSection((book,int(chapter),int(verse)))
		if (type(node) != int):
			node = 0
		print("...got node" + str(node))
		return node

	def getAPI(db='lxx'):
		if (db=='lxx'):
			api=LXX.api
			api.lex =lambda i : api.F.lex_utf8.v(i)
			theBooksDict=tfLxxBooksDict
		elif (enableNT and db=='nt'):
			api=NTa
			api.lex = lambda i: api.F.lemma.v(i)
			theBooksDict=ntBooksDict
		elif (enableBHS and db=='bhs'):
			api=BHS.api
			api.lex= lambda i : api.F.voc_lex_utf8.v(i) if api.F.voc_lex_utf8.v(i) else api.F.lex_utf8.v(i)
			theBooksDict=tfBhsBooksDict
			#api.lex =lambda i : api.F.lex_utf8.v(i)
		return api

	def getDicts(db='lxx'):
		if (db=='lxx'):
			return {'dict': posDict, 'groups': posGroups}
		elif(db=='bhs'):
			return {'dict': bhsPosDict, 'groups': bhsPosGroups}

	def sectionFromNode(node,db='lxx'):
		api=LXX.api
		if (enableBHS and db=='bhs'):
			api=BHS.api
		section= api.T.sectionFromNode(node)
		string = ''
		if (len(section) == 3):
			string = str(section[0]) + " " + str(section[1]) + ":" + str(section[2])
		elif (len(section) == 2):
			string = str(section[0]) + " " + str(section[1])
		else:#book only:
			string = str(section[0])
		return string

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

		
	# returns dict of lexemes and frequencies:
	def getLexemes(sections=[], restrict=[],exclude=[], min=1, gloss=False, totalCount=True,pos=False,checkProper=True, beta=True,type='all',common=False, db='lxx',plain=False):
		#mylog("Min: " + str(min))
		#print("getLexmes.gloss: " + str(gloss))
		
		#print("getLexemes with sections = " + ",".join([str(s) for s in sections]) +"; common: " + str(common))
		#print("getLexemes().Restricted: " + ",".join([str(x) for x in restrict]))
		#print("getLexemes().Excluded: " + ",".join([str(x) for x in exclude]))
		api=getAPI(db)
		theDicts=getDicts(db)
		
		lexemes = {}
		sectionsLexemes = {}

		totalInstances = 0
		totalLexemes = 0
		totalWordsInSections = 0
		if (enableBHS and db=='bhs'):
			restrictStrings=[v['abbrev'] for (k,v) in theDicts['dict'].items() if k in restrict]
			excludeStrings=[v['abbrev'] for (k,v) in theDicts['dict'].items() if k in exclude]
		else:
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


			if (api.F.otype.v(wordid) == 'word'):
				#beta = F.lex.v(wordid)
				totalWordsInSections += 1
				#greek = F.lex_utf8.v(wordid)

				if (checkProper and ((db == 'lxx' and api.F.sp.v(wordid) == 'noun') and api.F.lex_utf8.v(wordid)[0].isupper())
					or db=='bhs' and api.F.sp.v(wordid) == 'nmpr'): 
					# we have a name, and must account for that fact:
					if ((not excluded or 26 not in exclude) 
						and (not restricted or 26 in restrict)): #we should include it
						include = True
				else:# don't need to worry about names
					thePos = api.F.sp.v(wordid)
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
					if (not api.lex(wordid) in lexemes.keys()):
						totalLexemes +=1
						lexemes[api.lex(wordid)] = {'count': 1, 'id': wordid}
						# track which of the give sections this word is in:
						if (common):
							sectionsLexemes[api.lex(wordid)]=set([int(s) for s in (set(L.u(wordid)) & set(sections))])

						if (totalCount):
							if (db=='lxx'):
								lexemes[api.lex(wordid)]['total'] = int(api.F.freq_lemma.v(wordid));
							elif(db=='bhs'):
								lexemes[api.lex(wordid)]['total'] = int(api.F.freq_lex.v(wordid));
						if (gloss):
							lexemes[api.lex(wordid)]['gloss'] = api.F.gloss.v(wordid)
						if (beta):
							lexemes[api.lex(wordid)]['beta'] = api.F.lex.v(wordid)
						if (pos):
							lexemes[api.lex(wordid)]['pos'] = api.F.sp.v(wordid)
							#print("Got pos!")
							if ((db == 'lxx' and lexemes[api.lex(wordid)]['pos'] == 'noun' and api.lex(wordid)[0].isupper())
								or (db == 'bhs' and lexemes[api.lex(wordid)]['pos']=='nmpr')):
								if (checkProper and db=='lxx'):
									lexemes[api.lex(wordid)]['pos'] = 'proper noun or name'
								else:
									lexemes[api.lex(wordid)]['proper'] = True
						if (plain and db=='bhs'):
							lexemes[api.lex(wordid)]['plain'] = api.F.lex_utf8.v(wordid)
					else:
						lexemes[api.lex(wordid)]['count'] += 1
						if (common):
							sectionsLexemes[api.lex(wordid)].update([int(s) for s in (set(api.L.u(wordid)) & set(sections))])
			
			id=int(nodeid)
			if (api.L.d(id) and not recursive):
				for w in api.L.d(id):
					addLexes(w,recursive=True)
			elif(api.F.otype.v(id) == 'word'):
				addLex(id)
			
		#print("sections: " + str(sections))
		if(len(sections) > 0):
			for s in sections:
				s=int(s)
				foundSuper = False
				for supersect in api.L.u(s):
					if ((str(supersect) in sections) or (supersect in sections)):
						foundSuper = True
				if(not foundSuper):
					addLexes(s)
		else:
			for o in api.N.walk():
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


	def genWordCloudSVG(freqDataDict, title='',maxWords=200):
		wc = WordCloud(font_path="lib/fonts/SBL_BibLit_Regular.ttf", background_color="white",width=800,height=600, max_words=maxWords)
		wc.generate_from_frequencies(freqDataDict)
		svg = wc.to_svg(embed_font=True)
		
		if(title):
			svg = svg.replace("</svg>",'<text font-size="50" style="text-decoration: underline; font-family: \'Arial\'; font-variant: small-caps; font-weight: bold" transform="translate(149,650)">' + title +'</text></svg>')
			svg = svg.replace('height="600"', 'height="700"')
		return svg


	def getChaptersDict(book, db='lxx'):
		mylog("getChapters(" + str(book) + "," + db +")")
		api = getAPI(db)
		return dict([(api.F.chapter.v(c), c) for c in api.L.d(book) if api.F.otype.v(c)=='chapter'])
		
	def getBooksDict(db='lxx'):
		api=getAPI(db)
		return dict([(b, api.F.book.v(b)) for b in api.N.walk() if api.F.otype.v(b) == 'book'])


	def getApp():
		return app
	return app
#app = create_app()