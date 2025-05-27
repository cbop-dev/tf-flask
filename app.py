import sys
#from tf.fabric import Fabric
from tf.app import use
from flask import Flask, request, Response
from wordcloud import WordCloud, STOPWORDS
from pathlib import Path
from flask_cors import CORS

enableNT=True
enableBHS=False
debug = False
def mylog(msg):
	if(debug):
		print(msg)

NT = None

if (enableBHS):
	BHS = use('etcbc/bhsa')
	bhsA = BHS.api

if (enableNT):
	NT = use('CenterBLC/N1904')
	NTa = NT.api

LXX = use("CenterBLC/LXX", version="1935", hoist=globals())

#app = Flask(__name__, subdomain_matching=True)
app = Flask(__name__)
#app.config['SERVER_NAME'] = "tf.cbop.faith:5000"
app.config['SERVER_NAME'] = "localhost.localdomain:5000"
CORS(app)

def getAPI(db='lxx'):
	if (db=='lxx'):
		api=LXX.api
		api.lex =lambda i : api.F.lex_utf8.v(i)
	elif (enableNT and db=='nt'):
		api=NTa
		api.lex = lambda i: api.F.lemma.v(i)
	elif (enableBHS and db=='bhs'):
		api=BHS.api
		api.lex= lambda i : api.F.voc_lex_utf8.v(i) if api.F.voc_lex_utf8.v(i) else api.F.lex_utf8.v(i)
		#api.lex =lambda i : api.F.lex_utf8.v(i)
	return api

def getDicts(db='lxx'):
	if (db=='lxx'):
		return {'dict': posDict, 'groups': posGroups}
	elif(db=='bhs'):
		return {'dict': bhsPosDict, 'groups': bhsPosGroups}


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
26:  {'abbrev': 'name', 'desc':  'proper noun or name'},
}

posGroups={
	"CONT":[0,1,2,3,4,5],
	"CONTENT":[0,1,2,3,4,5],
	"SYNT":list(range(17,26)),#NB: excludes last item
	"SYNTAX":list(range(17,26)),
	"PREP":[16,23,24],
	"PREPOSITIONS":[16,23,24],
	"PREPOSITION":[16,23,24],
	"PART":[19,25],#I'm not counting 13 (pers+part) or 24 (prep+part)
	"PARTICLES":[19,25],
	"PARTICLE":[19,25],
	"PRON":list(range(6,14)),
	"PRONOUNS":list(range(6,14)),
	"PRONOUN":list(range(6,14)),
	
}

if (enableBHS):
	bhsPosDict ={
	0: {'abbrev': 'subs', 'desc':'noun, substantive'},
	1: {'abbrev': 'nmpr', 'desc':'proper noun'},
	2: {'abbrev': 'verb', 'desc':'verb'},
	3: {'abbrev': 'adjv', 'desc':'adjective'},
	4: {'abbrev': 'advb', 'desc':'adverb'},
	5: {'abbrev': 'intj', 'desc':'interjection'},
	6: {'abbrev': 'prps', 'desc':'personal pronoun'},
	7: {'abbrev': 'prep', 'desc':'preposition'},
	8: {'abbrev': 'prde', 'desc':'demonstrative pronoun'},
	9: {'abbrev': 'inrg', 'desc':'interogative'},
	10: {'abbrev': 'conj', 'desc':'conjunction'},
	11: {'abbrev': 'nega', 'desc':'negative particle'},
	12: {'abbrev': 'prin', 'desc':'interogative pronoun'},
	13: {'abbrev': 'art', 'desc':'article'},	
	}
	tfBhsBooksDict = {
	426591:{"abbrev":"Gen","syn":["Genesis",'Gen','Ge']},
	426592:{"abbrev":"Exod","syn":["Exodus",'Exod','Exodus']},
	426593:{"abbrev":"Lev","syn":["Leviticus",'Lev','Leviticus']},
	426594:{"abbrev":"Num","syn":["Numeri",'Num','Numbers']},
	426595:{"abbrev":"Deut","syn":["Deuteronomium",'Deut','Deuteronomy','Dt','Deu']},
	426596:{"abbrev":"Josh","syn":["Josua",'Josh','Joshua',"Josua"]},
	426597:{"abbrev":"Judg","syn":["Judices",'Judg','Judges','Jdg','Jdgs',"Judgs"]},
	426598:{"abbrev":"1Sam","syn":["Samuel_I",'1Sam','1Samuel','ISamuel','1Sa','1Sam','ISa','ISam']},
	426599:{"abbrev":"2Sam","syn":["Samuel_II",'2Sam','2Samuel','IISamuel','2Sa','2Sam','IISa','IISam']},
	426600:{"abbrev":"1Kgs","syn":["Reges_I",'1Kgs','1Kings','IKings','1Kg','IKg']},
	426601:{"abbrev":"2Kgs","syn":["Reges_II",'2Kgs','2Kings','IIKings','2Kg','IIKg']},
	426602:{"abbrev":"Isa","syn":["Jesaia",'Isa','Isaiah','Is',"Jesaia"]},
	426603:{"abbrev":"Jer","syn":["Jeremia",'Jer','Jeremiah',"Jeremia","Jerem","Jere"]},
	426604:{"abbrev":"Ezek","syn":["Ezechiel",'Ezek','Ezekiel',"Ezechiel"]},
	426605:{"abbrev":"Hos","syn":["Hosea",'Hos']},
	426606:{"abbrev":"Joel","syn":["Joel"]},
	426607:{"abbrev":"Amos","syn":["Amos","Am"]},
	426608:{"abbrev":"Obad","syn":["Obadia",'Obad','Obadiah','Ob',"Obed"]},
	426609:{"abbrev":"Jonah","syn":["Jona",'Jonah','Jon']},
	426610:{"abbrev":"Mic","syn":["Micha",'Mic','Micah',"Micha","Mica"]},
	426611:{"abbrev":"Nah","syn":["Nahum",'Nah']},
	426612:{"abbrev":"Hab","syn":["Habakuk",'Hab','Habakkuk']},
	426613:{"abbrev":"Zeph","syn":["Zephania",'Zeph','Zephaniah']},
	426614:{"abbrev":"Hag","syn":["Haggai",'Hag','Haggai']},
	426615:{"abbrev":"Zech","syn":["Sacharia",'Zech','Zechariah']},
	426616:{"abbrev":"Mal","syn":["Maleachi",'Mal','Malachi']},
	426617:{"abbrev":"Ps","syn":["Psalmi",'Ps(s)','Psalms','Psa']},
	426618:{"abbrev":"Job","syn":["Iob",'Job','Jb']},
	426619:{"abbrev":"Prov","syn":["Proverbia",'Prov','Proverbs','Pr']},
	426620:{"abbrev":"Ruth","syn":["Ruth","Ru"]},
	426621:{"abbrev":"Cant","syn":["Canticum",'Song','SongofSongs','SongofSolomon','Canticles','Cant']},
	426622:{"abbrev":"Qoh","syn":["Ecclesiastes",'Eccl','Ecclesiastes','Qoheleth','Qoh',"Eccl"]},
	426623:{"abbrev":"Lam","syn":["Threni",'Lam','Lamentations']},
	426624:{"abbrev":"Esth","syn":["Esther",'Esth','Est']},
	426625:{"abbrev":"Dan","syn":["Daniel","Dan"]},
	426626:{"abbrev":"Ezra","syn":["Esra","Ezr"]},
	426627:{"abbrev":"Neh","syn":["Nehemia",'Nehemiah',"Neh"]},
	426628:{"abbrev":"1Chr","syn":["Chronica_I",'1Chr','1Chronicles','1Chron','1Ch','IChronicles','IChron','ICh','IChr']},
	426629:{"abbrev":"2Chr","syn":["Chronica_II",'2Chr','2Chronicles','2Chron','2Ch','IIChronicles','IIChron','IICh','IIChr']},
	}


	bhsPosGroups={
"CONT":[0,1,2,3,4],
	"CONTENT":[0,1,2,3,4],
	"SYNT":[10,11],
	"SYNTAX":[10,11],
	"PREP":[7],
	"PREPOSITIONS":[7],
	"PREPOSITION":[7],
	"PART":[5,9,11,13],#I'm counting the article as a particle
	"PARTICLES":[5,9,11,13],
	"PARTICLE":[5,9,11,13],
	"PRON":[6,8,12],
	"PRONOUNS":[6,8,12],
	"PRONOUN":[6,8,12],

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
	623702: {'abbrev': "1Sam", 'syn': ['1 Sam', '1 Samuel', 'I Samuel','1 Sa', '1 Sam','I Sa', 'I Sam','1 Kgdms', '1 Kingdoms','I Kingdoms','I Kgdms',]},
	623703: {'abbrev': "2Sam", 'syn': ['2 Sam', '2 Samuel', 'II Samuel','2 Sa', '2 Sam','II Sa', 'II Sam','2 Kgdms', '2 Kingdoms','II Kingdoms','II Kgdms', '2 Kgdms', '2 Kingdoms','II Kingdoms','II Kgdms']},
	623704: {'abbrev': "1Kgs", 'syn': ['1 Kgs', '1 Kings', 'I Kings','1 Kg', 'I Kg', '3 Kgdms', '3 Kingdoms','III Kingdoms','III Kgdms']},
	623705: {'abbrev': "2Kgs", 'syn': ['2 Kgs', '2 Kings', 'II Kings','2 Kg', 'II Kg', '4 Kgdms', '4 Kingdoms','IV Kingdoms','IV Kgdms']},
	623706: {'abbrev': "1Chr", 'syn': ['1 Chr', '1 Chronicles', '1 Chron', '1 Ch','I Chronicles', 'I Chron', 'I Ch','I Chr']},
	623707: {'abbrev': "2Chr", 'syn': ['2 Chr', '2 Chronicles', '2 Chron', '2 Ch', 'II Chronicles', 'II Chron', 'II Ch','II Chr']},
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

ntBooksDict={
137780 : {"abbrev": "Matt" , "syn": ["Matthew", "Mt" ,"Mtt", "Mat", "Matt"] , "words": 18299 , "lemmas": 1670 , "chapters": 28 },
137781 : {"abbrev": "Mark" , "syn": ["Mark","Mar","Mk","Mc"] , "words": 11277 , "lemmas": 1336 , "chapters": 16 },
137782 : {"abbrev": "Luke" , "syn": ["Luke", "Lk","Luk","Lu"] , "words": 19456 , "lemmas": 2031 , "chapters": 24 },
137783 : {"abbrev": "John" , "syn": ["John", "Jn", "Jo","Giov", "Iohn"] , "words": 15643 , "lemmas": 1023 , "chapters": 21 },
137784 : {"abbrev": "Acts" , "syn": ["Acts", "Act", "Ac"] , "words": 18393 , "lemmas": 2017 , "chapters": 28 },
137785 : {"abbrev": "Rom" , "syn": ["Romans", "Ro", "Rom"] , "words": 7100 , "lemmas": 1056 , "chapters": 16 },
137786 : {"abbrev": "1 Cor" , "syn": ["1 Corinthians","I Cor","1 Cor", "I Corinthians","I Co","1 Co","I_Cor","1_Cor","I_Corinthians","1_Corinthians","I_Co","1_Co"] , "words": 6820 , "lemmas": 950 , "chapters": 16 },
137787 : {"abbrev": "2 Cor" , "syn": ["2 Corinthians","II Cor","2 Cor", "II Corinthians","II Co","2 Co","II_Cor","2_Cor","II_Corinthinans","2_Corinthians","II_Co","2_Co"] , "words": 4469 , "lemmas": 784 , "chapters": 13 },
137788 : {"abbrev": "Gal" , "syn": ["Galatians", "Gal","Ga"] , "words": 2228 , "lemmas": 516 , "chapters": 6 },
137789 : {"abbrev": "Eph" , "syn": ["Ephesians", "Eph","Ephe", "Ep"] , "words": 2419 , "lemmas": 527 , "chapters": 6 },
137790 : {"abbrev": "Phil" , "syn": ["Philippians", "Phil", "Ph", "Philip", "Phili"] , "words": 1630 , "lemmas": 443 , "chapters": 4 },
137791 : {"abbrev": "Col" , "syn": ["Colossians", "Col", "Co"] , "words": 1575 , "lemmas": 429 , "chapters": 4 },
137792 : {"abbrev": "1 Thess" , "syn": ["1 Thessalonians", "I Thess","1 Thess", "I Thes","1 Thes","I The","1 The","I_Thess","1_Thess","I_Thes","1_Thes","I_The","1_The","I_Thessalonians"] , "words": 1473 , "lemmas": 361 , "chapters": 5 },
137793 : {"abbrev": "2 Thess" , "syn": ["2 Thessalonians","II Thess","2 Thess", "II Thes","2 Thes","II The","2 The","II_Thess","2_Thess","II_Thes","2_Thes", "II_The","2_The","II_Thessalonians" ] , "words": 822 , "lemmas": 249 , "chapters": 3 },
137794 : {"abbrev": "1 Tim" , "syn": ["1 Timothy", "I Tim","1 Tim","I Ti","1 Ti","I_Tim","1_Tim","I_Tim","1_Tim","I_Ti","1_Ti","I_Timothy"] , "words": 1588 , "lemmas": 536 , "chapters": 6 },
137795 : {"abbrev": "2 Tim" , "syn": ["2 Timothy","II Tim","2 Tim","II Ti","2 Ti","II_Tim","2_Tim","II_Tim","2_Tim", "II_Ti","2_Ti" , "II_Timothy" ] , "words": 1237 , "lemmas": 453 , "chapters": 4 },
137796 : {"abbrev": "Titus" , "syn": ["Titus", "Tit", "Ti"] , "words": 658 , "lemmas": 299 , "chapters": 3 },
137797 : {"abbrev": "Phlm" , "syn": ["Philemon", "Phlmn", "Phlm","Phln","Phmn"] , "words": 335 , "lemmas": 140 , "chapters": 1 },
137798 : {"abbrev": "Heb" , "syn": ["Hebrews", "Heb", "He", "Hebr"] , "words": 4955 , "lemmas": 1025 , "chapters": 13 },
137799 : {"abbrev": "Jas" , "syn": ["James", "Ja", "Jam", "Jame"] , "words": 1739 , "lemmas": 553 , "chapters": 5 },
137800 : {"abbrev": "1 Pet" , "syn": ["1 Peter", "I Pet","1 Pet","I Pe","1 Pe","I_Pet","1_Pet","I_Pet","1_Pet","I_Pe","1_Pe", "I Peter"] , "words": 1676 , "lemmas": 542 , "chapters": 5 },
137801 : {"abbrev": "2 Pet" , "syn": ["2 Peter","II Pet","2 Pet","II Pe","2 Pe","II_Pet","2_Pet","II_Pet","2_Pet", "II_Pe","2_Pe" , "II Peter"] , "words": 1098 , "lemmas": 396 , "chapters": 3 },
137802 : {"abbrev": "1 John" , "syn": ["1 John", "1 Jn", "I Jn", "I John"] , "words": 2136 , "lemmas": 233 , "chapters": 5 },
137803 : {"abbrev": "2 John" , "syn": ["2 John","2 Jn", "II Jn", "II John"] , "words": 245 , "lemmas": 95 , "chapters": 1 },
137804 : {"abbrev": "3 John" , "syn": ["3 John","3 Jn", "III Jn", "III John"] , "words": 219 , "lemmas": 108 , "chapters": 1 },
137805 : {"abbrev": "Jude" , "syn": ["Jude", "Jud"] , "words": 457 , "lemmas": 225 , "chapters": 1 },
137806 : {"abbrev": "Rev" , "syn": ["Revelation", "Rev","Apocalypse", "Apoc", "Ap", "Re","Apo"] , "words": 9832 , "lemmas": 910 , "chapters": 22 }
}




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

#@app.route("/test", subdomain="bhs")
@app.route("/bhs/test")
#@app.route("/test")
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


def getChaptersDict(book, db='lxx'):
	mylog("getChapters(" + str(book) + "," + db +")")
	api = getAPI(db)
	return dict([(api.F.chapter.v(c), c) for c in api.L.d(book) if api.F.otype.v(c)=='chapter'])
	
def getBooksDict(db='lxx'):
	api=getAPI(db)
	return dict([(b, api.F.book.v(b)) for b in api.N.walk() if api.F.otype.v(b) == 'book'])

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


def genWordCloudSVG(freqDataDict, title='',maxWords=200):
	wc = WordCloud(font_path="lib/fonts/SBL_BibLit_Regular.ttf", background_color="white",width=800,height=600, max_words=maxWords)
	wc.generate_from_frequencies(freqDataDict)
	svg = wc.to_svg(embed_font=True)
	
	if(title):
		svg = svg.replace("</svg>",'<text font-size="50" style="text-decoration: underline; font-family: \'Arial\'; font-variant: small-caps; font-weight: bold" transform="translate(149,650)">' + title +'</text></svg>')
		svg = svg.replace('height="600"', 'height="700"')
	return svg

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
	booksChaps={}
	booksDict = tfLxxBooksDict
    
	if (enableBHS and db == 'bhs'):
		booksDict = tfBhsBooksDict
	
	for bid in booksDict.keys():
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
@app.route("/<string:db>/texts/")
def textsRoute(db='lxx'):
	texts = []
	ids=request.args.get("sections").split(",")
	try:
		for id in ids:
			texts.append({'section':getRef(id,db), 'text':getText(id,db), 'id': int(id)})
	except:
		texts=[]
	return texts

	


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
