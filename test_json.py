import json

with open("src/data/olympiads.json", 'r') as file:
    data = json.load(file)

print([len(str(cap)) for cap in data])