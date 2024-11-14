from flask import Flask, request, Response
from tf.fabric import Fabric
from tf.app import use
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import io
import random
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import json  # try  'json.dumps(object)' to get json object from python.
# and 'object = json.loads(jsonString)' to load from json.

LXX = use("CenterBLC/LXX", version="1935", hoist=globals())


app = Flask(__name__)

'''
@app.route('/products', defaults={'product_id': "jack"})
@app.route('/products/<product_id>/')
def show_product(product_id='jill'):
	#return request.args.get('product_id')
	if (product_id):
		return product_id
	else:
		return "nothing!"
'''

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



#@app.route("/")
def gen1():
	return LXX.api.T.text(655362)

@app.route("/test",defaults={'fred': None})
def test(fred):
	return fred


@app.route("/lex/freq/<int:lexid>")
def getLexCount(lexid):
	return LXX.api.Feature.freq_lemma.v(lexid)
	
# returns dict of lexemes and frequencies:
def getLexemes(sections=[], restrict=[],exclude=[]):
	
	lexemes = {}
	restrictStrings=[v['desc'] for (k,v) in posDict.items() if str(k) in restrict]
	print("restrictStrings: " + str(restrictStrings))
	restrict = True if len(restrictStrings) > 0 else False
	
	print("sections: " + str(sections))
	if(len(sections) > 0):
		for s in sections:
			s = int(s)
			for o in LXX.api.L.d(s):
				if(LXX.api.F.otype.v(o) == 'word' and (not restrict or (restrict and F.sp.v(o) in restrictStrings))):
					if (not F.lex_utf8.v(o) in lexemes.keys()):
						lexemes[F.lex_utf8.v(o)] = 1
					else:
						lexemes[F.lex_utf8.v(o)] += 1
				#words.append(F.lex_utf8.v(o))
	else:
		for o in N.walk():
			if(LXX.api.F.otype.v(o) == 'word' and not F.lex_utf8.v(o) in lexemes.keys()):
				lexemes[F.lex_utf8.v(o)] = F.freq_lemma.v(o)
				
	return lexemes


def getChaptersDict(book):
	return dict([(F.chapter.v(c), c) for c in L.d(book) if F.otype.v(c)=='chapter'])
	
def getBooksDict():
	return dict([(b, F.book.v(b)) for b in N.walk() if F.otype.v(b) == 'book'])

#@app.route("/books",view_func=bookss)


def noThang():
	return "Nothing"

@app.route("/wordcloud")
def wordCloudRoute():
	theLexemes=lexemesRoute()
	wc = WordCloud()
	wc.generate_from_frequencies(theLexemes)
	#fig = plt.figure(figsize=(10,6), dpi=600)
	#plt.imshow(wc, interpolation='bilinear')
	#plt.imshow(wc)
	#plt.axis("off")
	
	#plt.imshow(alice_mask, cmap=plt.cm.gray, interpolation='bilinear')
	#plt.axis("off")
	#plt.show()
	
	
	#fig = Figure()
	#axis = fig.add_subplot(1, 1, 1)
	#xs = range(100)
	#ys = [random.randint(1, 50) for x in xs]
	#axis.plot(xs, ys)
	#output = io.BytesIO()
	#FigureCanvas(fig).print_png(output)
	#return Response(output.getvalue(), mimetype='image/png')
	#return Response(output.getvalue(), mimetype='image/svg+xml')
	return Response(wc.to_svg(), mimetype='image/svg+xml')

	
	

@app.route("/lex")
def lexemesRoute():
	sections = request.args.get('sections').split(',') if ( request.args.get('sections')) else []
	restrict= request.args.get('restrict').split(',') if ( request.args.get('restrict')) else []
	return getLexemes(sections, restrict)

@app.route("/chapters/<int:book>")
def chaptersRoute(book):
	return getChaptersDict(book)

@app.route("/books")
def booksRoute():
	return getBooksDict()
	
routes={
	#"":getChaptersDict,
	#"/books": books,
	#"/lex": lexemesRoute,

	"/": gen1
}
	
for uri, func in routes.items():
	app.add_url_rule(uri,view_func=func)
	
#app.add_url_rule("/chapters/<int:book>", view_func=getChaptersDict)
#app.add_url_rule("/books", view_func=books)
    #return "<p>Hello, World!</p>"

