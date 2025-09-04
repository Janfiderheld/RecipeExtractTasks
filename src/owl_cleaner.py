from rdflib import Graph, URIRef, RDF, OWL, BNode
from rdflib.namespace import RDFS
from tqdm import tqdm

from src.extractor import get_all_subclasses


def remove_restriction_bnode(g, node):
    """Recursively delete a blank node and any linked blank nodes or RDF lists"""
    if not isinstance(node, BNode):
        return

    has_prior_iri = URIRef("http://www.ease-crc.org/ont/SOMA.owl#has_prior_task")
    includes_iri = URIRef("http://www.ease-crc.org/ont/SOMA.owl#includes_task")
    TARGET_PROPERTIES = {has_prior_iri, includes_iri}

    # Check if this node is an OWL restriction
    types = set(g.objects(node, RDF.type))
    on_props = set(g.objects(node, OWL.onProperty))

    if OWL.Restriction in types and (on_props & TARGET_PROPERTIES):
        # Remove any nested RDF lists (intersection/union)
        for coll_pred in [OWL.intersectionOf, OWL.unionOf]:
            for lst in g.objects(node, coll_pred):
                remove_rdf_list(g, lst)

        # Remove all triples where node is subject or object
        for t in list(g.triples((node, None, None))):
            g.remove(t)
        for t in list(g.triples((None, None, node))):
            g.remove(t)

    else:
        # If node is not a restriction itself, check for nested collections
        for coll_pred in [OWL.intersectionOf, OWL.unionOf]:
            for lst in g.objects(node, coll_pred):
                for item in rdf_list_items(g, lst):
                    remove_restriction_bnode(g, item)


def remove_rdf_list(g, lst):
    """Recursively remove RDF list nodes"""
    while lst != RDF.nil:
        first_nodes = list(g.objects(lst, RDF.first))
        for f in first_nodes:
            if isinstance(f, BNode):
                remove_restriction_bnode(g, f)
            for t in list(g.triples((f, None, None))):
                g.remove(t)
        rest_nodes = list(g.objects(lst, RDF.rest))
        for r in rest_nodes:
            lst = r
        for t in list(g.triples((lst, None, None))):
            g.remove(t)


def rdf_list_items(g, lst):
    """Generator for items in RDF list"""
    while lst != RDF.nil:
        first = list(g.objects(lst, RDF.first))
        if first:
            yield first[0]
        rest = list(g.objects(lst, RDF.rest))
        if rest:
            lst = rest[0]
        else:
            break


def remove_includes_task(file_path):
    g = Graph()
    g.parse(file_path, format="xml")
    recipe_iri = URIRef("http://purl.org/ProductKG/RecipeOn#Recipe")

    rec_subclasses = get_all_subclasses(g, recipe_iri)
    for cls in tqdm(rec_subclasses, "Removing the current restrictions from all Recipe subclasses"):
        for pred in [OWL.equivalentClass, RDFS.subClassOf]:
            for node in list(g.objects(cls, pred)):
                remove_restriction_bnode(g, node)
    g.serialize(file_path, format="xml")


def remove_task_subclasses(g, task_iri):
    subclasses = get_all_subclasses(g, task_iri)
    for subclass in subclasses:
        remove_task_subclasses(g, subclass)
    for triple in list(g.triples((task_iri, None, None))):
        g.remove(triple)
    for triple in list(g.triples((None, None, task_iri))):
        g.remove(triple)
