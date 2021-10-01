'''
Last Modified: March 22, 2021
this script is intended to create an import compliant csv file 
by querying data from wikidata.org
'''
import pandas as pd
import json
from collections import OrderedDict
import requests, csv, sys, re


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Missing Parent QID")
    QID = sys.argv[1]
    #query to wikidata and make a dataframe
    try:
        url = 'https://query.wikidata.org/sparql'
        query = ("""
                SELECT DISTINCT ?childLabel ?childDescription
                WHERE
                {
                wd:""" + QID + """ wdt:P527 ?parent. 
                ?parent wdt:P527 ?child
                SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
                }
                order by asc(UCASE(str(?childLabel)))
                """)
        request = requests.get(url, params = {'format': 'json', 'query': query})
        data = request.json()
    except:
        print("cannot complete query")
    leaves = []
    for item in data['results']['bindings']:
        leaves.append(OrderedDict({
            'Label': item['childLabel']['value'],
            'Description': item['childDescription']['value']}))
    df = pd.DataFrame(leaves)
    df.to_csv("leaves.csv",index=False)


