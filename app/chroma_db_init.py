from chroma_db_managment import ChromaManager
import json



if __name__ == "__main__":
    with open("all_olympiads_strings.json", 'r') as file:
        data = json.load(file)
    manager = ChromaManager()

    manager.create_collection(strings=data, collection_name="raw_data")