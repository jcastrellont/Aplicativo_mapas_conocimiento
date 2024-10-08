import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import pandas as pd
import numpy as np
import nltk
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from keybert import KeyBERT
import warnings
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import tkinter as tk
from tkinter import messagebox

################################################################################
################################################################################
# FUNCIONES 
################################################################################
################################################################################


################################################################################
## Funciones para busqueda
################################################################################
    

# Función para realizar la búsqueda en Arxiv
def search_arxiv(query, max_results=1000):
    base_url = "http://export.arxiv.org/api/query?"
    params = {
        "search_query": query,  # Término de búsqueda
        "start": 0,             # Desde qué resultado empezar
        "max_results": max_results,  # Número máximo de resultados
        "sortBy": "relevance",   # Ordenar por relevancia
        "sortOrder": "descending"  # Orden descendente
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        return response.text  # La respuesta en formato XML
    else:
        print(f"Error al hacer la consulta: {response.status_code}")
        return None

# Función para parsear y extraer títulos, abstracts y fechas de publicación (eliminado DOI)
def extract_paper_data(xml_data):
    root = ET.fromstring(xml_data)
    ns = {'arxiv': 'http://www.w3.org/2005/Atom'}  # Espacio de nombres en XML
    
    papers = []
    
    for entry in root.findall('arxiv:entry', ns):
        title = entry.find('arxiv:title', ns).text.strip()
        abstract = entry.find('arxiv:summary', ns).text.strip()
        published_date = entry.find('arxiv:published', ns).text.strip()
        
        papers.append({
            "title": title, 
            "abstract": abstract, 
            "published_date": published_date
        })
    
    return papers

# Función para filtrar por fecha
def filter_by_date(papers, start_date=None, end_date=None):
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    filtered_papers = []
    for paper in papers:
        pub_date = datetime.strptime(paper['published_date'], "%Y-%m-%dT%H:%M:%SZ")
        if (not start_date or pub_date >= start_date) and (not end_date or pub_date <= end_date):
            filtered_papers.append(paper)
    
    return filtered_papers

# Función principal para buscar, filtrar y convertir a DataFrame
def get_arxiv_papers_df(query, max_results=1000, start_date=None, end_date=None):
    print(f"Buscando artículos en Arxiv sobre '{query}'...")
    xml_data = search_arxiv(query, max_results)
    
    if xml_data:
        papers = extract_paper_data(xml_data)
        print(f"Se han encontrado {len(papers)} artículos.")
        
        # Aplicar el filtro por fecha
        if start_date or end_date:
            papers = filter_by_date(papers, start_date, end_date)
            print(f"Se han encontrado {len(papers)} artículos después de aplicar el filtro de fecha.")
        
        # Convertir a DataFrame
        df = pd.DataFrame(papers)
        return df
    else:
        print("No se pudo obtener información.")
        return pd.DataFrame()

# Función para solicitar datos al usuario
def user_input():
    query = input("Introduce el tema de búsqueda: ")
    start_date = input("Introduce la fecha de inicio (YYYY-MM-DD): ")
    end_date = input("Introduce la fecha de fin (YYYY-MM-DD): ")
    max_results = int(input("Introduce el número máximo de resultados: "))
    name = input("Asigne un nombre para el Mapa de conocimiento generado: ") 
    
    return query, start_date, end_date, max_results, name

################################################################################
## Procesamiento de datos
################################################################################

def process_text(text):
    stop_words = set(stopwords.words('english'))
    ps = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    # Tokenization
    tokens = text.split()
    
    # Remove punctuation and lower casing
    tokens = [word.lower() for word in tokens if word.isalnum()]
    
    # Stop words removal
    filtered_tokens = [word for word in tokens if word not in stop_words]
    
    # Stemming
    stemmed_tokens = [ps.stem(word) for word in filtered_tokens]
    
    # Lemmatization
    lemmatized_tokens = [lemmatizer.lemmatize(word) for word in stemmed_tokens]
    
    # Convert tokens back to a single string
    processed_text = ' '.join(lemmatized_tokens)
    
    return processed_text

################################################################################
## Palabras Clave
################################################################################

### TF-IDF

def tfidf_extractor(carac,data):
    docs=data[carac+"_transformed"].tolist()
    cv=CountVectorizer(max_df=0.85,stop_words='english')
    word_count_vector=cv.fit_transform(docs)
    tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True)
    tfidf_transformer.fit(word_count_vector)
    def sort_coo(coo_matrix):
        tuples = zip(coo_matrix.col, coo_matrix.data)
        return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)
    def extract_topn_from_vector(feature_names, sorted_items, topn=10):
        """get the feature names and tf-idf score of top n items"""
        
        #use only topn items from vector
        sorted_items = sorted_items[:topn]
    
        score_vals = []
        feature_vals = []
        
        # word index and corresponding tf-idf score
        for idx, score in sorted_items:
            
            #keep track of feature name and its corresponding score
            score_vals.append(round(score, 3))
            feature_vals.append(feature_names[idx])
    
        #create a tuples of feature,score
        #results = zip(feature_vals,score_vals)
        results= {}
        for idx in range(len(feature_vals)):
            results[feature_vals[idx]]=score_vals[idx]
        
        return results
    # you only needs to do this once, this is a mapping of index to 
    feature_names=cv.get_feature_names_out()
    # Añade las columnas para los tres principales keywords
    data[carac+'_keyword_TFIDF1'] = ''
    data[carac+'_keyword_TFIDF2'] = ''
    data[carac+'_keyword_TFIDF3'] = ''
    
    # Itera sobre cada fila del DataFrame
    for i in range(len(data)):
        doc = data.loc[i, carac+"_transformed"]
    
        # Genera tf-idf para el documento actual
        tf_idf_vector = tfidf_transformer.transform(cv.transform([doc]))
    
        # Ordena los vectores tf-idf por puntaje en orden descendente
        sorted_items = sort_coo(tf_idf_vector.tocoo())
    
        # Extrae los tres principales keywords
        keywords = extract_topn_from_vector(feature_names, sorted_items, 3)
    
        # Asigna los keywords a las columnas correspondientes
        try:
            data.at[i, carac+'_keyword_TFIDF1'] = list(keywords.keys())[0]
        except:
            data.at[i, carac+'_keyword_TFIDF1'] = ''
        try:
            data.at[i, carac+'_keyword_TFIDF2'] = list(keywords.keys())[1]
        except:
            data.at[i, carac+'_keyword_TFIDF2'] = ''
        try:
            data.at[i, carac+'_keyword_TFIDF3'] = list(keywords.keys())[2]
        except:
            data.at[i, carac+'_keyword_TFIDF3'] = ''
    return(data)

### KeyBERT

def keybert_keywords(carac,data):
    kw_model = KeyBERT()
    aa=kw_model.extract_keywords(docs=list(data[carac+'_transformed']), keyphrase_ngram_range=(1,3))
    results = [[key for key, prob in sorted(sublist, key=lambda x: x[1], reverse=True)[:1]] for sublist in aa]
    data[carac+'_keyword_keybert']=results
    data[carac+'_keyword_keybert']=data[carac+'_keyword_keybert'].str[0]
    return(data)

################################################################################
## KMEANS
################################################################################

def kmeans(dataframe, clusters=30):
    df_clusters=dataframe[['keywords_total']]
    df_clusters['keywords_total']=df_clusters['keywords_total'].astype(str)
    #define vectorizer parameters
    vectorizer = TfidfVectorizer(ngram_range=(1,1))
    
    # Generate matrix of word vectors
    tfidf_matrix = vectorizer.fit_transform(df_clusters['keywords_total'])
    ###############################################
    # k-means clustering
    ###############################################
    

    
    mod = KMeans(clusters, random_state=123)
    
    model=mod.fit(tfidf_matrix )
    dataframe['cluster_kmeans']=model.predict(tfidf_matrix)
    dataframe['cluster_kmeans']='cluster_'+dataframe['cluster_kmeans'].astype(str)
    contador = Counter(model.predict(tfidf_matrix))
    magnitud_nodo=pd.DataFrame(contador.items(), columns=['cluster_kmeans', 'cantidad'])
    magnitud_nodo['cluster_kmeans']=['cluster_'+str(magnitud_nodo['cluster_kmeans'][i]) for i in range(len(magnitud_nodo))]
    return dataframe, magnitud_nodo
    
################################################################################
## Procesamiento Final
################################################################################

def final_process(dataframe, magnitud_nodo):
    data_agrup = dataframe.groupby('cluster_kmeans').agg({
                                                            'title': ' '.join,
                                                            'abstract': ' '.join
                                                        }).reset_index()
    data_agrup['total_text']=data_agrup['title']+' '+data_agrup['abstract']
    data_agrup["total_text_tr"] = data_agrup["total_text"].apply(process_text)
    kw_model = KeyBERT()
    aa=kw_model.extract_keywords(docs=list(data_agrup['total_text_tr']), keyphrase_ngram_range=(1,3))
    results = [[key for key, prob in sorted(sublist, key=lambda x: x[1], reverse=True)[:1]] for sublist in aa]
    data_agrup['Grupo_keyBERT']=results
    data_agrup['Grupo_keyBERT']=data_agrup['Grupo_keyBERT'].str[0]
    data_agrup=data_agrup.merge(magnitud_nodo)
    return data_agrup

################################################################################
## Indicadores de similitud
################################################################################

def similarities_df(data_agrup):
    similarities=data_agrup[['cluster_kmeans','Grupo_keyBERT']]
    similarities['key']=1
    cross=data_agrup[['Grupo_keyBERT']].rename(columns={'Grupo_keyBERT':'Grupo_keyBERT_2'})
    cross['key']=1
    similarities=similarities.merge(cross).drop('key',axis=1)
    similarities=similarities[similarities['Grupo_keyBERT']!=similarities['Grupo_keyBERT_2']].reset_index(drop=True)
    # Vectorización TF-IDF
    vectorizer = TfidfVectorizer()
    
    # Convertir la columna 'texto1' en una matriz TF-IDF
    tfidf_matrix1 = vectorizer.fit_transform(similarities['Grupo_keyBERT'])
    
    # Convertir la columna 'texto2' en una matriz TF-IDF
    tfidf_matrix2 = vectorizer.transform(similarities['Grupo_keyBERT_2'])
    
    # Calcular la similitud coseno entre los vectores de 'texto1' y 'texto2'
    cosine_similarities = []
    for i in range(len(similarities)):
        cosine_sim = cosine_similarity(tfidf_matrix1[i], tfidf_matrix2[i])
        cosine_similarities.append(cosine_sim[0][0])
    
    # Agregar la similitud coseno como una nueva columna en el DataFrame
    similarities['sim_coseno'] = cosine_similarities
    similarities['disim_coseno']=1-similarities['sim_coseno']
    top_frame=similarities[(similarities['sim_coseno']!=0)&(similarities['sim_coseno']!=1)]
    top_frame['sim_coseno']=(top_frame['sim_coseno']-top_frame['sim_coseno'].min())/(top_frame['sim_coseno'].max()-top_frame['sim_coseno'].min())
    data_agrup2=data_agrup[(data_agrup['Grupo_keyBERT'].isin(top_frame['Grupo_keyBERT'].unique()))]
    return top_frame, data_agrup2

################################################################################
## Resultado final
################################################################################

def mapas_conocimiento(dataframe):
    dataframe["title_transformed"] = dataframe["title"].apply(process_text)
    dataframe["abstract_transformed"] = dataframe["abstract"].apply(process_text)
    dataframe=tfidf_extractor('abstract',dataframe)
    dataframe=tfidf_extractor('title',dataframe)
    dataframe=keybert_keywords('abstract',dataframe)
    dataframe=keybert_keywords('title',dataframe)
    dataframe['keywords_total']=dataframe['abstract_keyword_TFIDF1']+' '+dataframe['abstract_keyword_TFIDF2']+' '+dataframe['abstract_keyword_TFIDF3']+' '+dataframe['title_keyword_TFIDF1']\
                        +' '+dataframe['title_keyword_TFIDF2']+' '+dataframe['title_keyword_TFIDF3']+' '+dataframe['abstract_keyword_keybert']+' '+dataframe['title_keyword_keybert']
    lista_obj_0,lista_obj_1=kmeans(dataframe)
    dataframe=lista_obj_0
    data_agrup=final_process(dataframe,lista_obj_1)
    lista_obj2_0,lista_obj2_1=similarities_df(data_agrup)
    similarities=lista_obj2_0
    data_agrup2=lista_obj2_1
    return similarities, data_agrup2

################################################################################
## Mapas de conocimiento
################################################################################

def mapa(top_frame, data_agrup2, name, query):
    # Crear un grafo vacío
    G = nx.Graph()
    
    # Añadir nodos con tamaños proporcionales al número de elementos
    for _, row in data_agrup2.iterrows():
        G.add_node(row['Grupo_keyBERT'], size=row['cantidad'])
    
    # Añadir aristas con pesos proporcionales al índice de similitud
    for _, row in top_frame.iterrows():
        G.add_edge(row['Grupo_keyBERT'], row['Grupo_keyBERT_2'], weight=row['sim_coseno'])
    
    # Obtener tamaños de los nodos para visualización
    sizes = [G.nodes[node]['size']*50 for node in G.nodes()]
    
    # Obtener pesos de las aristas para visualización
    weights = [G[u][v]['weight'] * 10 for u, v in G.edges()]
    
    # Dibujar el grafo
    pos = nx.spring_layout(G)  # Posiciones de los nodos
    
    plt.figure(figsize=(15, 12))
    
    # Dibujar los nodos con tamaños proporcionales al número de elementos
    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color='lightblue', alpha=0.8)
    
    # Dibujar las aristas con grosores proporcionales a la similitud, y añadir curvas
    nx.draw_networkx_edges(G, pos, node_size=1000, width=weights, edge_color='lightgray', 
                           connectionstyle='arc3,rad=0.7')  # Aquí se curva la arista
    
    # Añadir etiquetas a los nodos
    nx.draw_networkx_labels(G, pos, font_size=8, font_color='black')
    
    # Mostrar el gráfico
    plt.title("Mapa de Conocimiento: "+str(query))
    plt.axis('off')  # Desactivar los ejes

    plt.savefig('mapas/'+str(name)+'.png')
    return plt

################################################################################
## Aplicativo para mapas
################################################################################

def ejecutable_aplicativo():
    # Función para ejecutar el código con los parámetros ingresados
    def ejecutar_busqueda():
        query = query_entry.get()
        start_date = start_date_entry.get()
        end_date = end_date_entry.get()
        max_results = max_results_entry.get()
        nombre = nombre_entry.get()
    
        if not query or not start_date or not end_date or not max_results or not nombre:
            messagebox.showwarning("Campos incompletos", "Por favor, completa todos los campos.")
            return
    
        try:
            max_results = int(max_results)  # Asegurar que sea un número
            # Ejecutar las funciones del código original
            df_papers = get_arxiv_papers_df(query, max_results, start_date, end_date)
            input_0, input_1 = mapas_conocimiento(df_papers)
            mapa(input_0, input_1, nombre, query)
            messagebox.showinfo("Éxito", "El mapa de conocimiento se ha construido correctamente.")
        except ValueError:
            messagebox.showerror("Error", "Asegúrate de que el número máximo de resultados sea un valor entero.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
    
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Aplicativo de Construcción de Mapas de Conocimiento")
    
    # Crear los campos de entrada
    tk.Label(root, text="Palabra clave:").grid(row=0, column=0)
    query_entry = tk.Entry(root)
    query_entry.grid(row=0, column=1)
    
    tk.Label(root, text="Fecha de inicio (YYYY-MM-DD):").grid(row=1, column=0)
    start_date_entry = tk.Entry(root)
    start_date_entry.grid(row=1, column=1)
    
    tk.Label(root, text="Fecha de fin (YYYY-MM-DD):").grid(row=2, column=0)
    end_date_entry = tk.Entry(root)
    end_date_entry.grid(row=2, column=1)
    
    tk.Label(root, text="Número máximo de resultados:").grid(row=3, column=0)
    max_results_entry = tk.Entry(root)
    max_results_entry.grid(row=3, column=1)
    
    tk.Label(root, text="Nombre del mapa:").grid(row=4, column=0)
    nombre_entry = tk.Entry(root)
    nombre_entry.grid(row=4, column=1)
    
    # Botón para ejecutar la búsqueda
    tk.Button(root, text="Buscar y construir mapa", command=ejecutar_busqueda).grid(row=5, column=0, columnspan=2)
    
    # Iniciar el loop de la ventana
    root.mainloop()
