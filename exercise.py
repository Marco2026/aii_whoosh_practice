import shutil
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
    res = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operaciÃ³n puede ser lenta")
    if res:
        save_data()

def save_data():
    schem = Schema(
        title=TEXT(stored=True, phrase=False),
        comensales=NUMERIC(int, stored=True), # Mejor para rangos y exactitud
        author=ID(stored=True),              # Mejor para búsquedas de nombres exactos
        update_date=DATETIME(stored=True),
        additional_features=KEYWORD(stored=True, commas=True, lowercase=True), # KEYWORD con commas=True para buscar etiquetas separadas como un todo
        introduction=TEXT(stored=True, phrase=False)
    )
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    ix= create_in("Index", schema=schem)
    writer = ix.writer()
    i= 0
    data = read_data()
    for recipe in data:
        writer.add_document(title=recipe[0], 
                            guests=int(recipe[1]), 
                            author=recipe[2] if recipe[2] else 'Unknown', 
                            update_date=recipe[3] if recipe[3] else datetime.now(), 
                            additional_features=recipe[4] if recipe[4] else 'None', 
                            introduction=recipe[5] if recipe[5] else 'None')
        i+=1
    writer.commit()
    messagebox.showinfo("Fin de indexado", "Se han indexado {} recetas".format(i))

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