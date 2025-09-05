import json

from rdflib import Graph, Namespace, URIRef, RDF, OWL, BNode, Literal
from rdflib.collection import Collection
from rdflib.namespace import RDFS
from tqdm import tqdm

from src.extractor import spacy_model, create_action_map
from src.owl_cleaner import remove_task_subclasses

ACTION_LIST = "./data/actions_map.json"


def write_updated_actions(file_path):
    g = Graph()
    g.parse(file_path, format="xml")
    # Todo: Update to use MEAL-based namespace
    namespace = Namespace("http://purl.org/ProductKG/recipe-instructions#")
    TASK = URIRef("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Task")
    remove_task_subclasses(g, TASK)

    with open(ACTION_LIST, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    for key, values in task_data.items():
        key_class = namespace[key]
        g.add((key_class, RDFS.subClassOf, TASK))
        for value in values:
            value_participle = to_participle(value)
            if key.lower() == value_participle.lower():
                continue
            value_class = namespace[value_participle]
            g.add((value_class, RDFS.subClassOf, key_class))
    g.serialize(file_path, format="xml")


def to_participle(word: str) -> str:
    doc = spacy_model(word)
    lemma = doc[0].lemma_

    if lemma.endswith("ie"):
        participle = lemma[:-2] + "ying"
    elif lemma.endswith("e") and not lemma.endswith("ee"):
        participle = lemma[:-1] + "ing"
    else:
        participle = lemma + "ing"
    return participle.capitalize()


# Define a method to find a class by its Reci:id annotation
def find_class_by_id(g, id, PRODUCTKG):
    for s, p, o in g.triples((None, PRODUCTKG.id, Literal(id))):
        if (s, RDF.type, OWL.Class) in g:
            return s
    return None


# Define a method to write the extracted verbs to the ontology
def write_to_owl(data, file_path, output_path):
    # Load the ontology
    g = Graph()
    g.parse(file_path, format="xml")

    # Define the relevant namespaces
    PRODUCTKG = Namespace("http://purl.org/ProductKG/RecipeOn#")
    SOMA = Namespace("http://www.ease-crc.org/ont/SOMA.owl#")
    RECIPE_INSTRUCTIONS = Namespace("http://purl.org/ProductKG/recipe-instructions#")
    TASK = URIRef("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Task")
    g.bind("recipeon", PRODUCTKG)
    g.bind("soma", SOMA)
    g.bind("instructions", RECIPE_INSTRUCTIONS)

    action_map = create_action_map(g, TASK)

    # Add the verbs to the ontology
    for recipe in tqdm(data, "Match the verbs and write results to ontology"):
        target_class = find_class_by_id(g, recipe['id'], PRODUCTKG)
        if target_class is None:
            print(f"Warning: Class with ID {recipe['id']} does not exist. Skipping addition.")
            continue

        for i in range(len(recipe['verbs'])):
            task_name = recipe['verbs'][i]
            task_participle = to_participle(task_name)

            # Skip tasks that are not in the task URI map (should not happen)
            if task_participle not in action_map:
                print(f"Warning: Task '{task_name}' not found in task URI map. Skipping.")
                continue
            task_uri = action_map[task_participle]

            # Add the first instruction as a single restriction
            if i == 0:
                add_single(target_class, g, "includes_task", task_uri, SOMA)

            # Add subsequent instructions as an intersection of restrictions
            else:
                previous_task_name = recipe['verbs'][i - 1]
                previous_task_participle = to_participle(previous_task_name)
                # Skip tasks that are not in the task URI map (should not happen)
                if previous_task_participle not in action_map:
                    print(f"Warning: Task '{previous_task_name}' not found in task URI map. Skipping.")
                    continue
                previous_task_uri = action_map[previous_task_participle]

                # Add the intersection of the previous and current tasks
                add_multiple(target_class, g, [
                    ("has_prior_task", previous_task_uri),
                    ("includes_task", task_uri)
                ], SOMA)

    # Write the modified ontology back to a file
    g.serialize(destination=output_path, format="xml")
    print(f"Modified ontology saved to {output_path}.")


# Define a method to add a single restriction
def add_single(target_class, g, property_type, task_uri, SOMA):
    property_uri = URIRef(SOMA[property_type])

    # Create a restriction for the single task
    task_restriction = BNode()
    g.add((task_restriction, RDF.type, OWL.Restriction))
    g.add((task_restriction, OWL.onProperty, property_uri))
    g.add((task_restriction, OWL.someValuesFrom, task_uri))

    # Add this restriction as an `rdfs:subClassOf` of the target class
    g.add((target_class, RDFS.subClassOf, task_restriction))


# Define a method to add multiple restrictions as an intersection
def add_multiple(target_class, g, tasks, SOMA):
    task_restrictions = []
    intersection_node = BNode()

    # Create a restriction for each task and add it to the intersection
    for property_type, task_uri in tasks:
        property_uri = URIRef(SOMA[property_type])

        # Create a restriction for each task
        task_restriction = BNode()
        g.add((task_restriction, RDF.type, OWL.Restriction))
        g.add((task_restriction, OWL.onProperty, property_uri))
        g.add((task_restriction, OWL.someValuesFrom, task_uri))

        # Collect each restriction for the intersection
        task_restrictions.append(task_restriction)

    # Use Collection to create an RDF list of the task restrictions
    collection_node = BNode()  # Root of the RDF list
    Collection(g, collection_node, task_restrictions)

    # Define the intersection of all task restrictions
    g.add((intersection_node, RDF.type, OWL.Class))
    g.add((intersection_node, OWL.intersectionOf, collection_node))

    # Add the intersection as a subclass of the target class
    g.add((target_class, RDFS.subClassOf, intersection_node))
