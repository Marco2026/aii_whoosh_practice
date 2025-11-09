import shutil
import pathlib, os, ssl, urllib.request, re
from datetime import datetime
from bs4 import BeautifulSoup
from tkinter import *
from tkinter import messagebox
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME, NUMERIC
from whoosh.qparser import MultifieldParser, QueryParser, OrGroup
from whoosh import qparser, index, query


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context=ssl._create_unverified_context


base_dir = pathlib.Path(__file__).parent.resolve()
indexdir = base_dir / 'indexdir'


def read_data():
    def obtain_recipes_uris():
        uris = []
        uri = "https://www.recetasgratis.net/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
        f = urllib.request.urlopen(uri)
        s = BeautifulSoup(f.read().decode('UTF-8'), "lxml")
        container = s.find("div", class_="clear padding-left-1")
        url_divs = container.find_all("a", href=True)
        for ud in url_divs:
            uris.append(ud['href'])
        print(uris)
        return uris

    def obtain_recipes_from_uris(recipes_uris):
        def parse_update_date(update_date):
            months = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'}
            slices = update_date.lower().split()
            slices = [slices[-3], slices[-2], slices[-1]]
            modified_date = f"{slices[0]} {months[slices[1]]} {slices[2]}"
            return datetime.strptime(modified_date, '%d %m %Y').strftime('%Y%m%d')
        
        def parse_guests(guests):
            return int(guests[:2].strip())
        
        def parse_additional_features(additional_features_soup):
            additional_features = ''
            if additional_features_soup:
                additional_features_soup = additional_features_soup.text.replace('Características adicionales:', '')
                sliced_features = additional_features_soup.split(',')
                additional_features = ', '.join([c.strip() for c in sliced_features])
            return additional_features

        recipes = list()
        for r in recipes_uris:
            raw_data = urllib.request.urlopen(r).read().decode('UTF-8')
            soup = BeautifulSoup(raw_data, 'lxml')
            title = soup.find('h1', class_='titulo titulo--articulo').text.strip() if soup.find('h1', class_='titulo titulo--articulo') else 'Unknown'
            guests = soup.find('span', class_='property comensales').text.strip() if soup.find('span', class_='property comensales') else '-1'
            author = soup.find('div', class_='nombre_autor').a.text.strip() if soup.find('div', class_='nombre_autor').a else 'Unknown'
            update_date = soup.find('span', class_='date_publish').text.strip() if soup.find('span', class_='date_publish') else 'Unknown'
            additional_features = soup.find('div', class_='properties inline') if soup.find('div', class_='properties inline') else 'Unknown'
            introduction = soup.find('div', class_='intro').text.strip() if soup.find('div', class_='intro') else 'Unknown'
            recipe = (title, parse_guests(guests), author, parse_update_date(update_date), parse_additional_features(additional_features), introduction)
            print(recipe)
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
        guests=NUMERIC(int, stored=True), # Mejor para rangos y exactitud
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

def list_results(results):
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in results:
        s = 'TITLE: ' + row['title']
        lb.insert(END, s)       
        s = 'GUESTS: ' + str(row['guests'])
        lb.insert(END, s)
        s = "AUTHOR: " + row['author']
        lb.insert(END, s)
        s = "UPDATE DATE: " + str(row['update_date'])
        lb.insert(END, s)
        s = "ADDITIONAL FEATURES: " + str(row['additional_features'])
        lb.insert(END, s)
        lb.insert(END,"------------------------------------------------------------------------\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

def main_window():
    def list_all():
        ix=open_dir("Index")
        with ix.searcher() as searcher:
            results = searcher.search(query.Every(),limit=None)
            list_results(results)
    
    root = Tk()
    menu = Menu(root)

    # DATA
    datamenu = Menu(menu, tearoff=0)
    datamenu.add_command(label="Load", command=load)
    datamenu.add_command(label="List", command=list_all)
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
    main_window()