'''
Last Modified: March 27, 2021
this script is intended to create an import compliant csv file  of the 
pathway 
by querying data from wikidata.org
'''

import pandas as pd
import json
import requests
import requests, csv, sys, re
from time import sleep
from collections import OrderedDict

def filter_children_string(str1):
    char_filter_out = "[]' "
    for c in char_filter_out:
        str1 = str1.replace(c, '')
    return str1
    
def child_query(pathway):
    return ("""
    SELECT ?child ?childLabel
    WHERE
    {
    wd:""" + pathway + """ wdt:P527 ?child. 
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    GROUP BY ?child ?childLabel
    """)

def label_query(pathway):
    return ("""
    SELECT ?label
        WHERE
        {
        wd:""" + pathway + """ rdfs:label ?label.
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
    """)
    
def description_query(pathway):
    return ("""
    SELECT ?description
        WHERE
        {
        wd:Q45317172 schema:description ?description. 
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
    """)
    
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Missing Pathway QID")
    pathway = sys.argv[1]
    try:
        master_list = pd.read_csv("master_list.csv")
    except:
        print("could not read master_list.csv")
    
    pathway_export_df = pd.DataFrame(columns = ["Label", "Description", "P4:wikibase-item"])
    url = 'https://query.wikidata.org/sparql'
    #query for child
    query = child_query(pathway)
    label_query = label_query(pathway)
    description_query = description_query(pathway)

    label_request = requests.get(url, params = {'format': 'json', 'query': label_query})
    sleep(1)
    description_request = requests.get(url, params = {'format': 'json', 'query': description_query})
    sleep(1)
    query_request = requests.get(url, params = {'format': 'json', 'query': query})

    label_temp = label_request.json()
    description_temp = description_request.json()
    query_temp = query_request.json()
    label = label_temp['results']['bindings'][0]['label']['value']
    description = description_temp['results']['bindings'][0]['description']['value']
    children_str = ""
    error_data = []
    for idx, item in enumerate(query_temp['results']['bindings']):
        child_label = item['childLabel']['value']
        child_qid = list(master_list.loc[master_list['Label'] == child_label]['QID'])
        if child_qid == "":
            error_data.append(child_qid)
            continue
        children_str = children_str + str(child_qid)
        if (idx + 1) % len(query_temp['results']['bindings']):
            children_str = children_str + "::"
    children_str = filter_children_string(children_str)
    new_row = {"Label":label, "Description":description, "P4:wikibase-item":children_str}
    pathway_export_df = pathway_export_df.append(new_row, ignore_index = True)
    pathway_export_df.to_csv(pathway+"pathway_import.csv", index = False)
    