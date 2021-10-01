import pandas as pd
import json
import requests, csv, sys, re
from time import sleep
from collections import OrderedDict

def filter_children_string(str1):
    char_filter_out = "[]' "
    for c in char_filter_out:
        str1 = str1.replace(c, '')
    return str1

def queryPathway(pathway):
    return ("""
    SELECT ?pathway ?pathwayLabel ?pathwayDescription
    WHERE
    {
    wd:""" + pathway + """ wdt:P527 ?pathway. #Glycolysis has part
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    GROUP BY ?pathway ?pathwayLabel ?pathwayDescription
    """)

def queryChildren(qid):
    return ("""
        SELECT ?child ?childLabel
        WHERE
        {
        wd:""" + qid + """ wdt:P527 ?child. 
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        GROUP BY ?child ?childLabel
        """)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Missing Pathway QID")
    pathway = sys.argv[1]
    try:
        master_list = pd.read_csv("master_list.csv")
    except:
        print("could not read master_list.csv")

    #create the dataframe that holds the reactions involved in pathway
    url = 'https://query.wikidata.org/sparql'
    query = queryPathway(pathway)
    r = requests.get(url, params = {'format': 'json', 'query': query})
    data = r.json()
    leaves = []
    error_data = []
    #iterate through all pathway reactions
    for item in data['results']['bindings']:
        leaves.append(OrderedDict({
            'Label': item['pathwayLabel']['value'],
            'Description': item['pathwayDescription']['value'],
            'QID': item['pathway']['value']}))
    query_df = pd.DataFrame(leaves)
    query_df["QID"] = query_df["QID"].str.strip("http://www.wikidata.org/entity/")
    export_df = pd.DataFrame(columns = ["Label", "Description", "P4:wikibase-item"])
    #get the reactants involved int pathway reactions and format correctly
    for index, row in query_df.iterrows():
        label = row["Label"]
        description = row["Description"]
        qid = row["QID"]
        query = queryChildren(qid)
        
        sleep(1) #sleep was added to fix querying bug
        try:
            r = requests.get(url, params = {'format': 'json', 'query': query})
            temp_data = r.json()
        except: 
            print("could not complete query on: " + label)
            error_data.append(label)
        children_str = ""
        for idx, item in enumerate(temp_data['results']['bindings']):
            child_label = item['childLabel']['value']
            child_qid = list(master_list.loc[master_list['Label'] == child_label]['QID'])
            children_str = children_str + str(child_qid)
            if (idx + 1) % len(temp_data['results']['bindings']):
                children_str = children_str + "::"
        
        children_str = filter_children_string(children_str)
        new_row = {"Label":label, "Description":description, "P4:wikibase-item":children_str}
        export_df = export_df.append(new_row, ignore_index = True)
        export_df.to_csv(pathway+"_nodes_import.csv", index=False)
    if(len(error_data) > 0):
        print("Could not properly add the following to" + pathway+"_reactant_import.csv:")
        print(error_data)

