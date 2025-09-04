import json

from rdflib import Graph, Namespace, URIRef, RDF, OWL, BNode, Literal
from rdflib.collection import Collection
from rdflib.namespace import RDFS

from src.extractor import spacy_model
from src.owl_cleaner import remove_task_subclasses

ACTION_LIST = "./data/actions_map.json"


def write_updated_actions(file_path):
    g = Graph()
    g.parse(file_path, format="xml")
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
    elif len(lemma) > 2 and lemma[-1] not in "aeiou" and lemma[-2] in "aeiou" and lemma[-3] not in "aeiou":
        participle = lemma + lemma[-1] + "ing"
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
    POURING_LIQUIDS = Namespace("http://www.ease-crc.org/ont/pouring_liquids#")
    FOOD_CUTTING = Namespace("http://www.ease-crc.org/ont/food_cutting#")
    CUT_SLICE_DICE = Namespace("http://www.ease-crc.org/ont/SOMA.owl#")
    g.bind("recipeon", PRODUCTKG)
    g.bind("soma", SOMA)
    g.bind("instructions", RECIPE_INSTRUCTIONS)

    # Define a mapping of task names to their corresponding URIs
    task_uri_map = {
        # food_arranging tasks
        "Arranging": RECIPE_INSTRUCTIONS["Arranging"],
        "Balancing": RECIPE_INSTRUCTIONS["Balancing"],
        "Changing": RECIPE_INSTRUCTIONS["Changing"],
        "Collecting": RECIPE_INSTRUCTIONS["Collecting"],
        "Crumbling": RECIPE_INSTRUCTIONS["Crumbling"],
        "Disposing": RECIPE_INSTRUCTIONS["Disposing"],
        "Finding": RECIPE_INSTRUCTIONS["Finding"],
        "Gathering": RECIPE_INSTRUCTIONS["Gathering"],
        "Grounding": RECIPE_INSTRUCTIONS["Grounding"],
        "Inserting": RECIPE_INSTRUCTIONS["Inserting"],
        "Introducing": RECIPE_INSTRUCTIONS["Introducing"],
        "Ladling": RECIPE_INSTRUCTIONS["Ladling"],
        "Laying": RECIPE_INSTRUCTIONS["Laying"],
        "Locating": RECIPE_INSTRUCTIONS["Locating"],
        "Picking": RECIPE_INSTRUCTIONS["Picking"],
        "Piling": RECIPE_INSTRUCTIONS["Piling"],
        "Placing": RECIPE_INSTRUCTIONS["Placing"],
        "Positioning": RECIPE_INSTRUCTIONS["Positioning"],
        "Putting": RECIPE_INSTRUCTIONS["Putting"],
        "Reaching": RECIPE_INSTRUCTIONS["Reaching"],
        "Setting": RECIPE_INSTRUCTIONS["Setting"],
        "Sticking": RECIPE_INSTRUCTIONS["Sticking"],
        "Throwing": RECIPE_INSTRUCTIONS["Throwing"],

        # food_mixing tasks
        "Admixing": RECIPE_INSTRUCTIONS["Admixing"],
        "Aggregating": RECIPE_INSTRUCTIONS["Aggregating"],
        "Amalgamating": RECIPE_INSTRUCTIONS["Amalgamating"],
        "Blending": RECIPE_INSTRUCTIONS["Blending"],
        "Coalescing": RECIPE_INSTRUCTIONS["Coalescing"],
        "Combining": RECIPE_INSTRUCTIONS["Combining"],
        "Commingleing": RECIPE_INSTRUCTIONS["Commingleing"],
        "Commixing": RECIPE_INSTRUCTIONS["Commixing"],
        "Compounding": RECIPE_INSTRUCTIONS["Compounding"],
        "Concocting": RECIPE_INSTRUCTIONS["Concocting"],
        "Conflating": RECIPE_INSTRUCTIONS["Conflating"],
        "Fusing": RECIPE_INSTRUCTIONS["Fusing"],
        "Grouping": RECIPE_INSTRUCTIONS["Grouping"],
        "Integrating": RECIPE_INSTRUCTIONS["Integrating"],
        "Intermixing": RECIPE_INSTRUCTIONS["Intermixing"],
        "Melding": RECIPE_INSTRUCTIONS["Melding"],
        "Merging": RECIPE_INSTRUCTIONS["Merging"],
        "Mingling": RECIPE_INSTRUCTIONS["Mingling"],
        "Mixing": RECIPE_INSTRUCTIONS["Mixing"],
        "Pairing": RECIPE_INSTRUCTIONS["Pairing"],
        "Shaking": RECIPE_INSTRUCTIONS["Shaking"],
        "Unifying": RECIPE_INSTRUCTIONS["Unifying"],

        # food_cutting tasks
        "Preparing": FOOD_CUTTING["Preparing"],
        "Filletting": FOOD_CUTTING["Filletting"],
        "Crosscutting": FOOD_CUTTING["Crosscutting"],
        "Jagging": FOOD_CUTTING["Jagging"],
        "Incising": FOOD_CUTTING["Incising"],
        "Slashing": FOOD_CUTTING["Slashing"],
        "Slitting": FOOD_CUTTING["Slitting"],
        "Cutting": CUT_SLICE_DICE["Cutting"],
        "Carving": FOOD_CUTTING["Carving"],
        "Paring": FOOD_CUTTING["Paring"],
        "Sawing": FOOD_CUTTING["Sawing"],
        "Severing": FOOD_CUTTING["Severing"],
        "Trenching": FOOD_CUTTING["Trenching"],
        "Dicing": CUT_SLICE_DICE["Dicing"],
        "Chopping": FOOD_CUTTING["Chopping"],
        "Cubing": FOOD_CUTTING["Cubing"],
        "Slicing": CUT_SLICE_DICE["Slicing"],
        "Slivering": FOOD_CUTTING["Slivering"],
        "Snipping": FOOD_CUTTING["Snipping"],
        "Halving": FOOD_CUTTING["Halving"],
        "Julienning": FOOD_CUTTING["Julienning"],
        "Mincing": FOOD_CUTTING["Mincing"],
        "Quartering": FOOD_CUTTING["Quartering"],
        "Trisecting": FOOD_CUTTING["Trisecting"],

        # pouring_liquids tasks
        "Draining": POURING_LIQUIDS["Draining"],
        "Cascading": POURING_LIQUIDS["Cascading"],
        "Flowing": POURING_LIQUIDS["Flowing"],
        "Pouring": POURING_LIQUIDS["Pouring"],
        "Spilling": POURING_LIQUIDS["Spilling"],
        "Splashing": POURING_LIQUIDS["Splashing"],
        "Sprinkling": POURING_LIQUIDS["Sprinkling"],
        "Streaming": POURING_LIQUIDS["Streaming"]
    }

    # Add the verbs to the ontology
    for recipe in data:
        target_class = find_class_by_id(g, recipe['id'], PRODUCTKG)
        if target_class is None:
            print(f"Warning: Class with ID {recipe['id']} does not exist. Skipping addition.")
            continue

        for i in range(len(recipe['verbs'])):
            task_name = recipe['verbs'][i]
            task_uri = task_uri_map.get(task_name)

            # Skip tasks that are not in the task URI map (should not happen)
            if not task_uri:
                print(f"Warning: Task '{task_name}' not found in task URI map. Skipping.")
                continue

            # Add the first instruction as a single restriction
            if i == 0:
                add_single(target_class, g, "includes_task", task_uri, SOMA)

            # Add subsequent instructions as an intersection of restrictions
            else:
                previous_task_name = recipe['verbs'][i - 1]
                previous_task_uri = task_uri_map.get(previous_task_name)

                # Skip tasks that are not in the task URI map (should not happen)
                if not previous_task_uri:
                    print(f"Warning: Task '{previous_task_name}' not found in task URI map. Skipping.")
                    continue

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
