import urllib.request
import re
import spacy
from neo4j import GraphDatabase, basic_auth

driver = GraphDatabase.driver(
  "bolt://<HOST>:<BOLTPORT>",
  auth=basic_auth("neo4j", "yousef"))


target_url = 'https://www.gutenberg.org/files/95/95-0.txt'

data = urllib.request.urlopen(target_url)
raw_data = data.read().decode('utf8').strip()
# Preprocess text into chapters
chapters = re.sub('[^A-z0-9 -]', ' ', raw_data).split('CHAPTER')[1:]
chapters[-1] = chapters[-1].split('End of the Project Gutenberg EBook')[0]


# import spacy and load a NLP model

nlp = spacy.load("en_core_web_lg", disable=["tagger", "parser"])
# Analyze the first chapter
c = chapters[0]
# Get a list of persons
doc = nlp(c)
involved = list(set([ent.text for ent in doc.ents if ent.label_ == 'PERSON']))
# replace names of involved in the text
# with an id and save the mapping
decode = dict()
for i, x in enumerate(involved):
    # Get mapping
    decode['$${}$$'.format(i)] = x
    # Preprocess text
    c = c.replace(x, ' $${}$$ '.format(i))

save_query = """
    MERGE (p1:Person{name:$name1})
    MERGE (p2:Person{name:$name2})
    MERGE (p1)-[r:RELATED]-(p2)
    ON CREATE SET r.score = 1
    ON MATCH SET r.score = r.score + 1"""
