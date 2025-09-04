import argparse
import json
import os

from src.extractor import process_words, extract_recipes_from_owl
from src.owl_cleaner import remove_includes_task
from src.writer import write_updated_actions, write_to_owl

DEFAULT_ONTO_PATH = 'data/recipe-ingredientset.owl'

def main(file_path, remove=False):
    if remove:
        remove_includes_task(file_path)
        write_updated_actions(file_path)

    # Extract the recipes from the OWL file
    recipes_json = json.loads(extract_recipes_from_owl(file_path))

    # Process the words using the word_prozessor function
    extracted_recipes = process_words(recipes_json)

    # Define the output path for the modified ontology
    root, extension = os.path.splitext(file_path)
    output_path = root + "_modified" + extension

    # Write the extracted verbs to the ontology
    write_to_owl(extracted_recipes, file_path, output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Bachelorthesis of Kasim Ali Shah, Extract Verbs from an OWL-File")
    parser.add_argument("--file_path", help="The path to the owl-file you want to process", default=DEFAULT_ONTO_PATH)
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Optional argument to remove previously added verbs from the ontology"
    )
    args = parser.parse_args()
    main(args.file_path, args.remove)
