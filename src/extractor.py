import json

import spacy
from rdflib import Graph, URIRef
from rdflib.namespace import RDFS

# Run the following command beforehand:
# python -m spacy download en_core_web_trf
spacy_model = spacy.load('en_core_web_trf')


# Extracts the Recipe and the corresponding ID into a JSON Format
def extract_recipes_from_owl(file_path):
    g = Graph()
    g.parse(file_path, format="xml")
    ID = URIRef("http://purl.org/ProductKG/RecipeOn#id")
    INSTR = URIRef("http://purl.org/ProductKG/RecipeOn#instructions")

    recipes = []
    for s, o in g.subject_objects(INSTR):
        recipes.append({
            "id": str(g.value(s, ID)),
            "instructions": str(o)
        })
    return json.dumps({"recipes": recipes}, indent=4)


def process_words(data):
    results = []
    for recipe in data['recipes']:
        instructions = recipe['instructions']
        verbs = []
        doc = spacy_model(instructions.lower())
        for sent in doc.sents:
            for token in sent:
                if token.pos_ == 'VERB':
                    verbs.append(remove_prefixes(token.lemma_))
        results.append({'id': recipe['id'], 'verbs': verbs})
    return results


def remove_prefixes(verb: str) -> str:
    prefixes = ['un', 're', 'in', 'im', 'dis', 'non', 'pre', 'post', 'mis', 'over', 'under', 'sub', 'super', 'anti',
                'inter']
    for prefix in prefixes:
        if verb.startswith(prefix):
            candidate = verb[len(prefix):]
            doc = spacy_model(candidate)
            if any(tok.pos_ == 'VERB' for tok in doc):
                return candidate
    return verb


def get_all_subclasses(g, class_uri):
    subclasses = set()
    direct = list(g.subjects(RDFS.subClassOf, class_uri))
    for s in direct:
        subclasses.add(s)
        subclasses.update(get_all_subclasses(g, s))
    return list(subclasses)
