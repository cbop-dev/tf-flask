import pytest, os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as app

lexes = app.getLexemes(sections=[623751,623752],common=True)
#print("; ".join(lexes['common']))

#print("hello world!")
#lexes = app.getLexemes(sections=[623694,623694],common=True)
#print(lexes['common'])

def test_getLex():
    # vocab of Genesis
    lexes = app.getLexemes(sections=[623694])
    assert lexes['totalLexemes'] == 2096
    assert len(list(lexes['lexemes'])) == 2096
    #print("hello")

def test_getCommonLexes():
    # Gen 1 and 2
    lexes = app.getLexemes(sections=[623751,623752],common=True)
    assert lexes['totalLexemes'] == 213
    
    assert len(list(lexes['lexemes'])) == 213

    assert len(lexes['common']) == 46
    #assert lexes['common'][0]=="fred"
    #assert type(lexes['common']) == 'list'

def test_getNodeFromSection():
    db='nt'
    start=382714
    end=382716
    expected = "Βίβλος γενέσεως Ἰησοῦ Χριστοῦ υἱοῦ Δαυεὶδ υἱοῦ Ἀβραάμ. Ἀβραὰμ ἐγέννησεν τὸν Ἰσαάκ, Ἰσαὰκ δὲ ἐγέννησεν τὸν Ἰακώβ, Ἰακὼβ δὲ ἐγέννησεν τὸν Ἰούδαν καὶ τοὺς ἀδελφοὺς αὐτοῦ,"
    output = app.getVersesFromNodeRange(start,end,db)
    assert (expected == output)