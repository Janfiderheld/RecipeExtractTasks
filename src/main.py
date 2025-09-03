import argparse
import json
import os
import xml.etree.ElementTree as ET

import nltk
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from rdflib import Graph, Namespace, URIRef, RDF, OWL, BNode, Literal
from rdflib.collection import Collection
from rdflib.namespace import RDFS

"""
Define the main class for the extraction, writing of verbs and removal of verbs from the ontology
The class contains two methods: extract_recipes_from_owl and word_prozessor
The extract_recipes_from_owl method extracts the recipes and their corresponding IDs from the OWL file
The word_prozessor method processes the extracted recipes and extracts the verbs from the instructions
The write_to_owl method writes the extracted verbs back to the ontology
The find_class_by_id method finds a class by its Reci:id annotation
The add_single method adds a single restriction to the ontology
The add_multiple method adds multiple restrictions as an intersection to the ontology
The main method is used to run the entire process
"""


class VerbExtractor:
    # Extracts the Recipe and the corresponding ID into a JSON Format
    @staticmethod
    def extract_recipes_from_owl(file_path):
        g = Graph()
        g.parse(file_path)
        ID = URIRef("http://purl.org/ProductKG/RecipeOn#id")
        INSTR = URIRef("http://purl.org/ProductKG/RecipeOn#instructions")

        recipes = []
        for s, o in g.subject_objects(INSTR):
            recipes.append({
                "id": str(g.value(s, ID)),
                "instructions": str(o)
            })
        return json.dumps({"recipes": recipes}, indent=4)

    @staticmethod
    def process_words(data):
        # Ensure that necessary NLTK resources are downloaded
        nltk.download('wordnet')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('punkt')

        # Lemmatizer to get verb forms
        lemmatizer = WordNetLemmatizer()

        # List of verbs in their gerund form
        verbs_list = [
            "Cutting", "Quartering", "Julienning", "Halving", "Dicing", "Slicing", "Snipping", "Slivering", "Sawing", "Paring", "Carving",
            "Mincing", "Cubing", "Chopping", "Cascading", "Flowing", "Pouring", "Draining", "Spilling", "Splashing", "Sprinkling", "Streaming",
            "Admixing", "Aggregating", "Amalgamating", "Blending", "Coalescing", "Combining", "Commingleing", "Commixing", "Compounding", 
            "Concocting", "Conflating", "Fusing", "Grouping", "Integrating", "Intermixing", "Melding", "Merging", "Mingling", "Mixing", 
            "Pairing", "Shaking", "Unifying",
            "Arranging", "Balancing", "Changing", "Collecting", "Crumbling", "Disposing", "Finding", "Gathering", "Grounding", "Inserting", 
            "Introducing", "Ladling", "Laying", "Locating", "Picking", "Piling", "Placing", "Positioning", "Putting", "Reaching", "Setting", 
            "Sticking", "Throwing"
        ]

        # Convert between treebank tags and wordnet tags
        def get_wordnet_pos(treebank_tag):
            if treebank_tag.startswith('V'):  # if its a Verb
                return wn.VERB  # return wordnet sign for Verb
            elif treebank_tag.startswith('N'):  # if its a Noun
                return wn.NOUN  # return wordnet sign for Noun
            return None

        # Function to extract verbs
        def extract_verbs(instruction):
            tokens = nltk.pos_tag(word_tokenize(instruction))
            verbs_found = []
            for token, pos in tokens:
                wordnet_pos = get_wordnet_pos(pos)
                # if Verb or Noun lemmatize and check if verb matches with verb_list
                if wordnet_pos == wn.VERB or wordnet_pos == wn.NOUN:
                    lemma = lemmatizer.lemmatize(token, wn.VERB)
                    for verb in verbs_list:
                        if lemma == lemmatizer.lemmatize(verb.lower(), wn.VERB):
                            if verb not in verbs_found:
                                verbs_found.append(verb)
            return verbs_found

        # Extract verbs from each instruction
        results = []
        for recipe in data['recipes']:
            instructions = recipe['instructions']
            verbs = []
            sentences = instructions.split('.')
            for sentence in sentences:
                extracted = extract_verbs(sentence.lower())
                verbs.extend(extracted)
            results.append({'id': recipe['id'], 'verbs': verbs})

        return results


class ResultWriter:
    # Define a method to find a class by its Reci:id annotation
    @staticmethod
    def find_class_by_id(g, id, PRODUCTKG):
        for s, p, o in g.triples((None, PRODUCTKG.id, Literal(id))):
            if (s, RDF.type, OWL.Class) in g:
                return s
        return None

    # Define a method to write the extracted verbs to the ontology
    @staticmethod
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
            target_class = ResultWriter.find_class_by_id(g, recipe['id'], PRODUCTKG)
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
                    ResultWriter.add_single(target_class, g, "includes_task", task_uri, SOMA)

                # Add subsequent instructions as an intersection of restrictions
                else:
                    previous_task_name = recipe['verbs'][i - 1]
                    previous_task_uri = task_uri_map.get(previous_task_name)

                    # Skip tasks that are not in the task URI map (should not happen)
                    if not previous_task_uri:
                        print(f"Warning: Task '{previous_task_name}' not found in task URI map. Skipping.")
                        continue

                    # Add the intersection of the previous and current tasks
                    ResultWriter.add_multiple(target_class, g, [
                        ("has_prior_task", previous_task_uri),
                        ("includes_task", task_uri)
                    ], SOMA)

        # Write the modified ontology back to a file
        g.serialize(destination=output_path, format="xml")
        print(f"Modified ontology saved to {output_path}.")

    # Define a method to add a single restriction
    @staticmethod
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
    @staticmethod
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


class TaskRemover:
    @staticmethod
    def remove_includes_task(file_path):
        # Parse the XML/OWL file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Define the namespaces
        namespaces = {
            'owl': "http://www.w3.org/2002/07/owl#",
            'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            'rdfs': "http://www.w3.org/2000/01/rdf-schema#"
        }

        # Iterate over all <owl:Class> elements directly
        for owl_class in root.findall(".//owl:Class", namespaces):
            # Find all <rdfs:subClassOf> elements within this <owl:Class>
            subclass_elements = owl_class.findall("rdfs:subClassOf", namespaces)

            # Collect elements to remove
            elements_to_remove = []
            for subclass in subclass_elements:
                # Check if it contains an <owl:onProperty> with "includes_task"
                on_property = subclass.find("owl:Restriction/owl:onProperty", namespaces)
                if on_property is not None and "includes_task" in on_property.get(f"{{{namespaces['rdf']}}}resource",
                                                                                  ""):
                    elements_to_remove.append(subclass)

            # Remove collected elements from the current <owl:Class>
            for element in elements_to_remove:
                owl_class.remove(element)

        # Write the modified XML back to the file
        tree.write(file_path, encoding="utf-8", xml_declaration=True)


def main(file_path, remove=False):
    if remove:
        TaskRemover.remove_includes_task(file_path)

    # Extract the recipes from the OWL file
    recipes_json = json.loads(VerbExtractor.extract_recipes_from_owl(file_path))

    # Process the words using the word_prozessor function
    extracted_recipes = VerbExtractor.process_words(recipes_json)

    # Define the output path for the modified ontology
    root, extension = os.path.splitext(file_path)
    output_path = root + "_modified" + extension

    # Write the extracted verbs to the ontology
    ResultWriter.write_to_owl(extracted_recipes, file_path, output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Bachelorthesis of Kasim Ali Shah, Extract Verbs from an OWL-File"
    )
    parser.add_argument("file_path", help="The path to the owl-file you want to process")
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Optional argument to remove previously added verbs from the ontology"
    )
    args = parser.parse_args()
    main(args.file_path, args.remove)