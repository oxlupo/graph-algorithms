import urllib.request
import re
import spacy
from neo4j import GraphDatabase, basic_auth

driver = GraphDatabase.driver(
  "bolt://localhost:7687",
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

# Get an array of words
ws = c.split()
l = len(ws)
# Iterate through words
for wi, w in enumerate(ws):
    # Skip if the word is not a person
    if not w[:2] == '$$':
        continue
    # Check next x words for any involved person
    x = 14
    for i in range(wi+1, wi+x):
        # Avoid list index error
        if i >= l:
            break
        # Skip if the word is not a person
        if not ws[i][:2] == '$$':
            continue
        # Store to Neo4j
        params = {'name1': decode[ws[wi]], 'name2': decode[ws[i]]}
        driver.session.run(save_query, params)
        print(decode[ws[wi]], decode[ws[i]])


pagerank ="""
CALL algo.pageRank('Person','RELATED',{direction:'BOTH'})
"""

louvain = """
CALL algo.louvain('Person','RELATED',{direction:'BOTH'})
"""
with driver.session() as session:
    session.run(pagerank)
    session.run(louvain)

cypher = "MATCH (p1:Person)-[r:RELATED]->(p2:Person) RETURN *"
labels_json = {
    "Person": {
        "caption": "name",
        "size": "pagerank",
        "community": "community"
    }
}
relationships_json = {
    "RELATED": {
        "thickness": "score",
        "caption": False
    }
}
driver.generate_vis("bolt://localhost:7687", "neo4j", "yousef", cypher, labels_json, relationships_json)