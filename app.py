import sys
from flask import Flask, request, Response
from tf.fabric import Fabric
from tf.app import use
from wordcloud import WordCloud, STOPWORDS
from pathlib import Path

LXX = use("CenterBLC/LXX", version="1935", hoist=globals())

app = Flask(__name__)


posDict={
0:  {'abbrev': 'n', 'desc':  'noun',},
1:  {'abbrev': 'v', 'desc':  'verb',},
2:  {'abbrev': 'adj', 'desc':  'adjective',},
3:  {'abbrev': 'adj1', 'desc':  'adjective, 1st declension, -??/-?/-?? pattern endings',},
4:  {'abbrev': 'adj3', 'desc': 'adjective, 3rd declension pattern endings',},
5:  {'abbrev': 'adv', 'desc': 'adverb',},
6:  {'abbrev': 'pers', 'desc': 'pronoun, personal/possessive',},
7:  {'abbrev': 'rel', 'desc':  'pronoun, relative',},
8:  {'abbrev': 'ar', 'desc':  'pronoun, article',},
9:  {'abbrev': 'demon', 'desc':  'pronoun, demonstrative',},
10:  {'abbrev': 'rel2', 'desc': 'pronoun, relative, ?????',},
11:  {'abbrev': 'c', 'desc': 'conjunction',},
12:  {'abbrev': 'prep', 'desc':  'preposition',},
13:  {'abbrev': 'part', 'desc': 'particle',},
14:  {'abbrev': 'num', 'desc':  'indeclinable number',},
15:  {'abbrev': 'intero', 'desc':  'pronoun, interrogative/indefinite',},
16:  {'abbrev': 'interj', 'desc':  'interjection',},
17:  {'abbrev': 'c+demon', 'desc':  'conjunction + pronoun, demonstrative',},
18:  {'abbrev': 'c+rel', 'desc': 'conjunction + pronoun, relative',},
19:  {'abbrev': 'c+part', 'desc': 'conjunction + particle',},
20:  {'abbrev': 'c+adv', 'desc': 'conjunction + adverb',},
21:  {'abbrev': 'ar+adj', 'desc': 'pronoun, article + adjective',},
22:  {'abbrev': 'pers+part', 'desc': 'pronoun, personal/possessive + particle',},
23:  {'abbrev': 'prep+adj', 'desc': 'preposition + adjective',},
24:  {'abbrev': 'prep+part', 'desc': 'preposition + particle',},
25:  {'abbrev': 'demon+n', 'desc':  'pronoun, demonstrative + noun'},
}

#indexed by the tf node ids, with various synonyms for searching/looking-up.
tfLxxBooksDict = {
	623694: {'abbrev': "Gen", 'syn': ['Gen', 'Genesis', 'Ge']},
	623695: {'abbrev': "Exod", 'syn': ['Exod', 'Exodus']},
	623696: {'abbrev': "Lev", 'syn': ['Lev', 'Leviticus']},
	623697: {'abbrev': "Num", 'syn': ['Num', 'Numbers']},
	623698: {'abbrev': "Deut", 'syn': ['Deut', 'Deuteronomy', 'Dt', 'Deu']},
	623699: {'abbrev': "Josh", 'syn': ['Josh', 'Joshua']},
	623700: {'abbrev': "Judg", 'syn': ['Judg', 'Judges', 'Jdg', 'Jdgs', "Judgs"]},
	623701: {'abbrev': "Ruth", 'syn': ['Ruth', 'Ruth']},
	623702: {'abbrev': "1Sam", 'syn': ['1 Sam', '1 Samuel', 'I Samuel','1 Sa', '1 Sam','I Sa', 'I Sam','1 Kgdms', '1 Kingdoms','I Kingdoms','I Kgdms', '2 Kgdms', '2 Kingdoms','II Kingdoms','II Kgdms']},
	623703: {'abbrev': "2Sam", 'syn': ['2 Sam', '2 Samuel', 'II Samuel','2 Sa', '2 Sam','II Sa', 'II Sam']},
	623704: {'abbrev': "1Kgs", 'syn': ['1 Kgs', '1 Kings', 'I Kings','1 Kg', 'I Kg', '3 Kgdms', '3 Kingdoms','III Kingdoms','III Kgdms']},
	623705: {'abbrev': "2Kgs", 'syn': ['2 Kgs', '2 Kings', 'II Kings','2 Kg', 'II Kg', '4 Kgdms', '4 Kingdoms','IV Kingdoms','IV Kgdms']},
	623706: {'abbrev': "1Chr", 'syn': ['1 Chr', '1 Chronicles', '1 Chron', '1 Ch','I Chronicales', 'I Chron', 'I Ch','I Chr']},
	623707: {'abbrev': "2Chr", 'syn': ['2 Chr', '2 Chronicles', '2 Chron', '2 Ch', 'II Chronicales', 'II Chron', 'II Ch','II Chr']},
	623708: {'abbrev': "1Esdr", 'syn': ['Ezra', 'Ezra', '1 Esdras', 'I Esdras', '1 Esdr', 'I Esdr']},
	623709: {'abbrev': "2Esdr", 'syn': ['Neh', 'Nehemiah',  '2 Esdras', 'II Esdras', '2 Esdr', 'II Esdr']},
	623710: {'abbrev': "Esth", 'syn': ['Esth', 'Esther', 'Est']},
	623711: {'abbrev': "Jdt", 'syn': ['Jdt', 'Judith']},
	623712: {'abbrev': "TobBA", 'syn': ['Tob', 'Tobit', 'Tob BA', 'Tobit BA']},
	623713: {'abbrev': "TobS", 'syn': ['Tob', 'Tobit','Tob S', 'Tobit S']},
	623714: {'abbrev': "1Mac", 'syn': ['1 Macc', '1 Maccabees', '1 Macc', '1 Mac', '1 Maccab', 'I Macc', 'I Mac', 'I Maccab' ]},
	623715: {'abbrev': "2Mac", 'syn': ['2 Macc', '2 Maccabees', '2 Macc', '2 Mac', '2 Maccab', 'II Macc', 'II Mac', 'II Maccab']},
	623716: {'abbrev': "3Mac", 'syn': ['3 Macc', '3 Maccabees', '3 Macc', '3 Mac', '3 Maccab', 'III Macc', 'III Mac', 'III Maccab']},
	623717: {'abbrev': "4Mac", 'syn': ['4 Macc', '4 Maccabees', '4 Macc', '4 Mac', '4 Maccab', 'IV Macc', 'IV Mac', 'IV Maccab']},
	623718: {'abbrev': "Ps", 'syn': ['Ps(s)', 'Psalms', 'Psa']},
	623719: {'abbrev': "Od", 'syn': ['Odes', 'Odes of Solomon','OdesSol','OdSol']},
	623720: {'abbrev': "Prov", 'syn': ['Prov', 'Proverbs', 'Pr']},
	623721: {'abbrev': "Qoh", 'syn': ['Eccl', 'Ecclesiastes', 'Qoheleth', 'Qoh']},
	623722: {'abbrev': "Cant", 'syn': ['Song', 'Song of Songs', 'Song of Solomon', 'Canticles', 'Cant']},
	623723: {'abbrev': "Job", 'syn': ['Job', 'Jb']},
	623724: {'abbrev': "Wis", 'syn': ['Wis', 'Wisdom of Solomon', 'Wisdom', 'Wisd']},
	623725: {'abbrev': "Sir", 'syn': ['Sir', 'Sirach', 'Ecclesiasticus', 'Ben Sira']},
	623726: {'abbrev': "PsSol", 'syn': ['Psalms of Solomon', 'Ps Sol', 'PsaSol', 'Psa Sol']},
	623727: {'abbrev': "Hos", 'syn': ['Hos', 'Hosea']},
	623728: {'abbrev': "Mic", 'syn': ['Mic', 'Micah']},
	623729: {'abbrev': "Amos", 'syn': ['Amos', 'Amos']},
	623730: {'abbrev': "Joel", 'syn': ['Joel', 'Joel']},
	623731: {'abbrev': "Jonah", 'syn': ['Jonah', 'Jon', 'JonLXX', 'Jon LXX','JonahLXX', 'Jonah LXX']},
	623732: {'abbrev': "Obad", 'syn': ['Obad', 'Obadiah', 'Ob']},
	623733: {'abbrev': "Nah", 'syn': ['Nah', 'Nahum']},
	623734: {'abbrev': "Hab", 'syn': ['Hab', 'Habakkuk']},
	623735: {'abbrev': "Zeph", 'syn': ['Zeph', 'Zephaniah']},
	623736: {'abbrev': "Hag", 'syn': ['Hag', 'Haggai']},
	623737: {'abbrev': "Zech", 'syn': ['Zech', 'Zechariah']},
	623738: {'abbrev': "Mal", 'syn': ['Mal', 'Malachi']},
	623739: {'abbrev': "Isa", 'syn': ['Isa', 'Isaiah', 'Is']},
	623740: {'abbrev': "Jer", 'syn': ['Jer', 'Jeremiah']},
	623741: {'abbrev': "Bar", 'syn': ['Bar', 'Baruch']},
	623742: {'abbrev': "EpJer", 'syn': ['Ep Jer','Epistle of Jeremiah']},
	623743: {'abbrev': "Lam", 'syn': ['Lam', 'Lamentations']},
	623744: {'abbrev': "Ezek", 'syn': ['Ezek', 'Ezekiel']},
	623745: {'abbrev': "Bel", 'syn': ['Bel and the Dragon','BelDrag']},
	623746: {'abbrev': "BelTh", 'syn': ['Bel and the Dragon Th','BelDragTh']},
	623747: {'abbrev': "Dan", 'syn': ['Dan', 'Daniel','DanLXX', 'DanielLXX','Dan LXX', 'Daniel LXX','DanOG', 'DanielOG','Dan OG', 'Daniel OG']},
	623748: {'abbrev': "DanTh", 'syn': ['Dan', 'Daniel','DanTh', 'DanielTh','Dan Th', 'Daniel Th']},
	623749: {'abbrev': "Sus", 'syn': ['Susanna', 'SusOG', 'Sus OG', 'SusannaOG','Susanna OG']},
	623750: {'abbrev': "SusTh", 'syn': ['Susanna Th','SusannaTh']},
}


@app.route("/lex/freq/<int:lexid>")
def getLexCount(lexid):
	return LXX.api.Feature.freq_lemma.v(lexid)
	
# returns dict of lexemes and frequencies:
def getLexemes(sections=[], restrict=[],exclude=[], min=1, gloss=False, totalCount=False):
	#print("Min: " + str(min))
	#print("getLexmes.gloss: " + str(gloss))
	
	
	lexemes = {}
	restrictStrings=[v['desc'] for (k,v) in posDict.items() if str(k) in restrict]
	
	print("restrictStrings: " + str(restrictStrings))
	restrict = True if len(restrictStrings) > 0 else False

	def addLexes(nodeid):
		def addLex(wordid):
			if(LXX.api.F.otype.v(wordid) == 'word' and (not restrict or (restrict and F.sp.v(wordid) in restrictStrings))):
					
				if (not F.lex_utf8.v(wordid) in lexemes.keys()):
					if (not totalCount):
						lexemes[F.lex_utf8.v(wordid)] = {'count': 1, 'id': wordid}
					else:#using total counts
						lexemes[F.lex_utf8.v(wordid)] = {'count': F.freq_lemma.v(wordid), 'id': wordid}
					if (gloss):
						lexemes[F.lex_utf8.v(wordid)]['gloss'] = F.gloss.v(wordid)
				elif (not totalCount): #only do this if we're tracking counts within the chosen sections.
					lexemes[F.lex_utf8.v(wordid)]['count'] += 1
		
		id=int(nodeid)
		if (L.d(id)):
			for w in L.d(int(id)):
				addLex(w)
		else:
			addLex(id)
		
	
	#print("sections: " + str(sections))
	if(len(sections) > 0):
		for s in sections:
			s = int(s)
			addLexes(s)
	else:
		for o in N.walk():
			addLexes(o)
	print(lexemes)			
	return lexemes if min == 1 else {k:v for (k,v) in lexemes.items() if int(v['count']) >= int(min)}


def getChaptersDict(book):
	return dict([(F.chapter.v(c), c) for c in L.d(book) if F.otype.v(c)=='chapter'])
	
def getBooksDict():
	return dict([(b, F.book.v(b)) for b in N.walk() if F.otype.v(b) == 'book'])


@app.route("/wordcloud")
def wordCloudRoute():
	theLexemes=lexemesRoute()
	filteredLexemes= {}
	if (not 'gloss' in list(theLexemes.values())[0].keys()):
		filteredLexemes = {k:int(v['count']) for (k,v) in theLexemes.items()}
	else:
		filteredLexemes = {v['gloss'].split(";")[0]:int(v['count']) for (k,v) in theLexemes.items()}
	#print(filteredLexemes)
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

	return response


def genWordCloudSVG(freqDataDict, title='',maxWords=200):
	wc = WordCloud(font_path="/home/cbrannan/.local/share/fonts/Tiro Typeworks/TrueType/SBL BibLit/SBL_BibLit_Regular.ttf", background_color="white",width=800,height=600, max_words=maxWords)
	wc.generate_from_frequencies(freqDataDict)
	svg = wc.to_svg(embed_font=True)
	
	if(title):
		svg = svg.replace("</svg>",'<text font-size="50" style="text-decoration: underline; font-family: \'Arial\'; font-variant: small-caps; font-weight: bold" transform="translate(149,650)">' + title +'</text></svg>')
		svg = svg.replace('height="600"', 'height="700"')
	return svg
	

@app.route("/lex")
def lexemesRoute():
	sections = request.args.get('sections').split(',') if ( request.args.get('sections')) else []
	restrict= request.args.get('restrict').split(',') if ( request.args.get('restrict')) else []
	if ('SUBS' in restrict):
		restrict.remove('SUBS')
		restrict = restrict + ['0','1','2','3','4','5']
		#print("added SUBS")
		#print("restrict: " + str(restrict))
	

	min= request.args.get('min') if ( request.args.get('min')) else 1
	gloss= True if ( request.args.get('gloss') and int(request.args.get('gloss')) != 0) else False
	#print("Gloss: " + str(gloss))
	return getLexemes(sections=sections, restrict=restrict, min=min, gloss=gloss)

@app.route("/chapters/")
def allChaptersRoute():
	booksChaps={}
	for bid in tfLxxBooksDict.keys():
		booksChaps[bid]=getChaptersDict(bid)
	return booksChaps

@app.route("/chapters/<int:book>")
def chaptersRoute(book):
	return getChaptersDict(book)

@app.route("/books")
def booksRoute():
	return getBooksDict()

def sectionFromNode(node):
	section= T.sectionFromNode(node)
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

		#print(bookHash)
		
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
