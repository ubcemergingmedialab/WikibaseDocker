# load the necessary libraries
from wikidataintegrator import wdi_core, wdi_login
import pandas as pd
import requests, csv, sys, re
import io

#bot login credentials
bot_user='Admin'
bot_pwd='bot@v385220noa4s82a1dn8jndslvefb13hr'

if __name__ == "__main__":
    #reading the data
    if len(sys.argv) == 1:
        print("Missing input CSV file")
    
    # load excel table to load into Wikibase
    try:
        csv_path = sys.argv[1]
        mydata = pd.read_csv(csv_path)
        csv_file = open(csv_path,'r', encoding="utf8")
        csv_reader = csv.DictReader(csv_file)
        complete_data = []
        errors_data = []
        master_data = []
    except:
        print("cannot load" + csv_path)
    try:
        logincreds = wdi_login.WDLogin(user=bot_user, pwd=bot_pwd, mediawiki_api_url="http://localhost:8181/w/api.php")
    except:
        print("cannot access import-bot")
    
    for row in csv_reader:
        row = dict(row)
        data = []
        #append the properties to the data list
        for key in row:
            #reads the property field (refer to add_properties.csv)
            if key.find(':') > -1 and key[0] == "P":
                PID, data_type = key.split(":") 
                #other data types:
                try:
                    #insert new properties here
                    if data_type.lower() == 'wikibase-item':
                        if row[key] is not None and row[key].strip() != '':
                            #this for loop is to check if there are multiple items to append
                            listOfValues = row[key].split("::")
                            for value in listOfValues:
                                statement = wdi_core.WDItemID(value=value, prop_nr=PID)
                                data.append(statement)
                except Exception as e:
                    print("There was an error with this setting the properites for this one, skipping:")
                    print(row)
                    print(e)
                    errors_data.append(row)
                    data = "error"
            if data == 'error':
                continue

        try:
            wd_item = wdi_core.WDItemEngine(data=data, mediawiki_api_url="http://localhost:8181/w/api.php")
            # set the label and description if exists
            if 'Label' in row:
                if row['Label'] is not None and row['Label'].strip() != '':
                    wd_item.set_label(row['Label'])
            if 'Description' in row:
                if row['Description'] is not None and row['Description'].strip() != '':
                    wd_item.set_description(row['Description'])
            # write
            r = wd_item.write(logincreds)
            # QID is returned
            row['QID'] = r
            print(row['QID'], row['Label'])
            complete_data.append(row)
            master_data.append({'Label':row['Label'], 'QID':row['QID']})
        except Exception as e:
            print("There was an error with setting the Label and description for this one, skipping:")
            print(row)
            print(e)
            errors_data.append(row)
            data = "error"

    csv_file.close()
    with io.open(csv_path+'_updated.csv','w', encoding="utf-8") as out:
        fieldnames = list(complete_data[0].keys())
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(complete_data)
    with open('master_list.csv','a', encoding="utf-8") as out:
        fieldnames = ['Label', 'QID']
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writerows(master_data)
    if len(errors_data) > 0:
        with open(csv_path+'_errors.csv','w', encoding="utf-8") as out:
            fieldnames = list(errors_data[0].keys())
            writer = csv.DictWriter(out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(errors_data)
