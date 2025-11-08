import pathlib, os, ssl, urllib.request, re
from datetime import datetime
from bs4 import BeautifulSoup
from tkinter import *
from tkinter import messagebox
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME
from whoosh.qparser import MultifieldParser, QueryParser, OrGroup


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context=ssl._create_unverified_context


base_dir = pathlib.Path(__file__).parent.resolve()
indexdir = base_dir / 'indexdir'


def read_data():
    def obtain_recipes_uris():
        uris = []
        uri = "https://www.recetasgratis.net/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
        f = urllib.request.urlopen(uri)
        s = BeautifulSoup(f, "lxml")
        container = s.find("div", class_="clear padding-left-1")
        url_divs = container.find_all("a", href=True)
        for ud in url_divs:
            uris.append(ud['href'])
        print(uris)
        return uris

    def obtain_recipes_from_uris(recipes_uris):
        recipes = list()
        for r in recipes_uris:
            raw_data = urllib.request.urlopen(r).read().decode('UTF-8')
            soup = BeautifulSoup(raw_data, 'lxml')
            title = soup.find('h1', class_='titulo titulo--articulo').text.strip() if soup.find('h1', class_='titulo titulo--articulo') else 'Unknown'
            guests = soup.find('span', class_='property unidades').text.strip() if soup.find('span', class_='property unidades') else 'Unknown'
            author = None
            update_date = None
            additional_features = None
            introduction = None
            recipe = (title, guests, author, update_date, additional_features, introduction)
            recipes.append(recipe)
        return recipes


    recipes_uris = obtain_recipes_uris()
    data = obtain_recipes_from_uris(recipes_uris)
    return data

def load():
    data = read_data()
    pass

def title_or_introduction():
    pass

def date():
    pass

def features_and_title():
    pass

def main_window():
    root = Tk()
    menu = Menu(root)

    # DATA
    datamenu = Menu(menu, tearoff=0)
    datamenu.add_command(label="Load", command=load)
    datamenu.add_command(label="Exit", command=root.quit)
    menu.add_cascade(label="Data", menu=datamenu)

    # SEARCH
    searchmenu = Menu(menu, tearoff=0)
    searchmenu.add_command(label="Author", command=title_or_introduction)
    searchmenu.add_command(label="Delete by summary", command=date)
    searchmenu.add_command(label="Date and title", command=features_and_title)    
    menu.add_cascade(label="Search", menu=searchmenu)

    root.config(menu=menu, background='lightblue', width=500, height=400)

    root.mainloop()

if __name__ == '__main__':
    read_data()