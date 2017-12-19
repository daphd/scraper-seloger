# -*- coding: utf-8 -*-
"""
Script to retrieve data from the site seloger.com
"""

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
import os
import matplotlib.pyplot as plt
import seaborn as sns

# working_dir = "C:/Users/Laetitia/Documents/Python Scripts/seloger_scraper"
# os.chdir(working_dir)


# Initialize variables
locality = []
price = []
room_nb = []
bedroom_nb = []
surface = []
acc_type = []


# Create a session (to avoid redirecting loop with requests.get())
s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'


# Loop over different pages
max_pages = 30
page = 1
while (page <= max_pages):
    url = ("http://www.seloger.com/list.htm?org=advanced_search&idtt=2&idtypebien=2,1&cp=75&tri=initial&LISTING-LISTpg=" +
           str(page) + "&naturebien=1,2,4")
    page += 1
    try:
        r = s.get(url)
    except:
        # Stop visiting pages
        break
    
    # Get information from the page
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # find all ads from the page
    annonces = soup.find_all("div", attrs={"class": "listing_infos"})
    
    for annonce in annonces:
        # get properties of the appartment
        locality.append(annonce.find("div", attrs={"class": "locality"}).get_text())
        price.append(annonce.find("div", attrs={"class": "price"}).find("a").get_text())
        
        property_list = annonce.find("ul", attrs={"class": "property_list"}).find_all("li")
        if (len(property_list) == 3):
            room_nb.append(property_list[0].get_text())
            bedroom_nb.append(property_list[1].get_text())
            surface.append(property_list[2].get_text())
        else:
            room_nb.append("")
            bedroom_nb.append("")
            surface.append("")
        acc_type.append(annonce.find("div", attrs={"class": "title"}).find("a").get_text())

rst = pd.DataFrame({"locality": locality,
                    "price": price,
                    "room_nb": room_nb,
                    "bedroom_nb": bedroom_nb,
                    "surface": surface,
                    "acc_type": acc_type})

new_names = rst.columns.values
new_names = [name + "_raw" for name in new_names]
rst.columns = new_names
    
# Write result to csv
rst.to_csv("results/seloger-paris-page1-to-30_raw.csv", sep=";", encoding="utf-8")


## clean results
# Functions to improve to take into account case with "," and multiple numbers
def clean_text(text):
    """
    Delete unnecessary space and characters
    """
    return(re.sub(" {2,}|\r|\n","", text))
def get_number(text):
    """
    Extract number from string.
    """
#    if (isinstance(text, str) or isinstance(text, unicode)):
    if True:
        text.replace(",",".")
        text = re.sub("\xa0","", text)
        rst = re.findall("[0-9]+\.{0,1}[0-9]*", text)
        if rst:
            rst = rst[0]
        else:
            rst = "nan"
    else:
        rst = text
    try:
        rst = float(rst)
    except:
        rst = float("nan")
    return(rst)


# surface match
surface_reg = re.compile(r"[0-9]+,*[0-9]*\sm")
bed_reg = re.compile(r"chb")
room_reg = re.compile(r"[0-9]+\sp")

def get_measure(row, reg):
    candidates = row[["room_nb_raw", "bedroom_nb_raw", "surface_raw"]]
    for candidate in candidates:
        if reg.findall(candidate):
            return(get_number(candidate))
    return(float("nan"))

def clean_df(df):
    df = df.copy()
    df["surface"] = rst.apply(lambda row: get_measure(row, surface_reg), axis=1)
    df["bedroom_nb"] = rst.apply(lambda row: get_measure(row, bed_reg), axis=1)
    df["room_nb"] = rst.apply(lambda row: get_measure(row, room_reg), axis=1)
    
    str_col = ["acc_type", "locality"]
    str_col_old = [name+"_raw" for name in str_col]
    df[str_col] = df[str_col_old].applymap(clean_text)
    
    df["price"] = df["price_raw"].map(get_number)
    
    return(df)

clean_rst = clean_df(rst)
clean_rst["price_m2"] = clean_rst["price"]/clean_rst["surface"]

clean_rst.plot(kind="box", subplots=True)
clean_rst.plot(x="locality", y="price", kind="box", use_index=False, subplots=True)
plt.show()

min(clean_rst.price_m2)

clean_rst["locality"].unique()




localities = clean_rst.locality.unique()
localities.sort()
clean_rst["locality"] = clean_rst["locality"].astype("category", categories=localities)

sns.boxplot(data=clean_rst, x="locality", y="price_m2", hue="acc_type")
plt.xticks(rotation=45)
plt.show()
sns.despine(offset=10, trim=True)

sns.boxplot(data=clean_rst, x="locality", y="price", hue="acc_type")
plt.xticks(rotation=45)
plt.show()

sns.barplot(data=clean_rst, x="locality", y="price", hue="acc_type")
plt.xticks(rotation=45)
plt.show()

sns.countplot(data=clean_rst, x="locality", hue="acc_type")
plt.xticks(rotation=-45)


g = sns.FacetGrid(clean_rst, row="locality")
g.map(plt.scatter, x="surface", y="price")

clean_rst.plot(kind="scatter", x="surface", y="price", hue="locality")
