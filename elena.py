import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

import streamlit as st
import pandas as pd

import os
from dotenv import load_dotenv

import faiss

from llama_index import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
)
from llama_index.vector_stores.faiss import FaissVectorStore

from llama_index import (
    VectorStoreIndex,
    get_response_synthesizer,
    )
from llama_index import QueryBundle

from llama_index.retrievers import VectorIndexRetriever
from llama_index.query_engine import RetrieverQueryEngine

from llama_index.schema import NodeWithScore

# Retrievers
from llama_index.retrievers import (
    BaseRetriever,
    VectorIndexRetriever,
    KeywordTableSimpleRetriever,
)

from typing import List

from llama_index import get_response_synthesizer
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.prompts import PromptTemplate

from llama_index import (
    VectorStoreIndex,
    SimpleKeywordTableIndex,
    SimpleDirectoryReader,
    ServiceContext,
    StorageContext,
)

import pandas as pd

from llama_index.query_engine import PandasQueryEngine

from llama_index import (
    VectorStoreIndex,
    SummaryIndex,
    SimpleDirectoryReader,
    ServiceContext,
    StorageContext,
)
from llama_index.tools.query_engine import QueryEngineTool

from llama_index import VectorStoreIndex
from llama_index.objects import ObjectIndex, SimpleToolNodeMapping

from llama_index.query_engine import ToolRetrieverRouterQueryEngine

import re

# Definiciones y clases (mantén tu CustomRetriever si es necesario)

class CustomRetriever(BaseRetriever):
    """Custom retriever that performs both semantic search and hybrid search."""

    def __init__(
        self,
        vector_retriever: VectorIndexRetriever,
        keyword_retriever: KeywordTableSimpleRetriever,
        mode: str = "AND",
    ) -> None:
        """Init params."""

        self._vector_retriever = vector_retriever
        self._keyword_retriever = keyword_retriever
        if mode not in ("AND", "OR"):
            raise ValueError("Invalid mode.")
        self._mode = mode

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query."""

        vector_nodes = self._vector_retriever.retrieve(query_bundle)
        keyword_nodes = self._keyword_retriever.retrieve(query_bundle)

        vector_ids = {n.node.node_id for n in vector_nodes}
        keyword_ids = {n.node.node_id for n in keyword_nodes}

        combined_dict = {n.node.node_id: n for n in vector_nodes}
        combined_dict.update({n.node.node_id: n for n in keyword_nodes})

        if self._mode == "AND":
            retrieve_ids = vector_ids.intersection(keyword_ids)
        else:
            retrieve_ids = vector_ids.union(keyword_ids)

        retrieve_nodes = [combined_dict[rid] for rid in retrieve_ids]

        return retrieve_nodes
    
# Cargar variables de entorno
load_dotenv()

st.info('Estamos avisando a Elena, un momento, por favor.', icon="ℹ️")

# Función para cargar datos (puedes ajustar esto según la estructura de tu archivo)
@st.cache_data
def cargar():
    documents = SimpleDirectoryReader("/test").load_data()
    
    return documents

# Función para filtrar outfits negros
def pregunta(query):
    # set Logging to DEBUG for more detailed outputs
    try:
        query_engine = index.as_query_engine()
        response = query_engine.query(query)
        return response.response
    except Exception as e:
        st.error(f"Ocurrió un error al procesar la consulta: {e}")
        return None

def fuente(response, documents):

    service_context = ServiceContext.from_defaults()

    node_parser = service_context.node_parser
    nodes = node_parser.get_nodes_from_documents(documents)

    # initialize storage context (by default it's in-memory)
    storage_context = StorageContext.from_defaults()
    storage_context.docstore.add_documents(nodes)

    vector_index = VectorStoreIndex(nodes, storage_context=storage_context)
    keyword_index = SimpleKeywordTableIndex(nodes, storage_context=storage_context)
    # define custom retriever
    vector_retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=2)
    keyword_retriever = KeywordTableSimpleRetriever(index=keyword_index)
    custom_retriever = CustomRetriever(vector_retriever, keyword_retriever)

    # define response synthesizer
    response_synthesizer = get_response_synthesizer()

    # assemble query engine
    custom_query_engine = RetrieverQueryEngine(
        retriever=custom_retriever,
        response_synthesizer=response_synthesizer,
    )

    QA_PROMPT_TMPL = (
        "Actua como un experto shopper assistant de la empresa MANGO\n"
        "Esta es la información de contexto"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Pregunta: {query_str}\n"
        "Tu respuesta (explicando los motivos de la elección): "
    )

    QA_PROMPT = PromptTemplate(QA_PROMPT_TMPL)

    # vector query engine
    vector_query_engine = RetrieverQueryEngine(
        retriever=vector_retriever,
        response_synthesizer=response_synthesizer,
    )
    # keyword query engine
    keyword_query_engine = RetrieverQueryEngine(
        retriever=keyword_retriever,
        response_synthesizer=response_synthesizer,
    )

    df = pd.read_csv("/Users/albertgillopez/Downloads/mango-challenge/datathon/dataset/product_data100.csv")

    st.write('👉 Estoy hablando con los diseñadores.')

    df_v1 = df.drop('des_agrup_color_eng', axis=1)
    df_v2 = df_v1.drop('des_product_category', axis=1)
    df_v2 = df_v2.drop('des_product_aggregated_family', axis=1)
    # df_v2 = df_v2.drop('des_product_family', axis=1)
    # df_v2 = df_v2.drop('des_line', axis=1)

    query_engine = PandasQueryEngine(df=df_v2, verbose=True)

    response = query_engine.query(response)

    summary_index = SummaryIndex(nodes, storage_context=storage_context)

    list_query_engine = summary_index.as_query_engine(
        response_mode="tree_summarize", use_async=True
    )
  
    list_tool = QueryEngineTool.from_defaults(
        query_engine=list_query_engine,
        description="Useful for product recommendation",
    )
    vector_tool = QueryEngineTool.from_defaults(
        query_engine=vector_query_engine,
        description=(
            "Useful for retrieving specific products of a provided recommendation"
        ),
    )

    tool_mapping = SimpleToolNodeMapping.from_objects([list_tool])
    obj_index = ObjectIndex.from_objects(
        [list_tool],
        tool_mapping,
        VectorStoreIndex,
    )

    query_engine = ToolRetrieverRouterQueryEngine(obj_index.as_retriever())

    response = query_engine.query(response.response)

    pandas_pregunta = response.response

    st.write('👉 No me lo estás poniendo nada fácil :(')

    query_engine = PandasQueryEngine(df=df_v2, verbose=True)

    response = query_engine.query(pandas_pregunta)

    return response, response.metadata["pandas_instruction_str"], df_v2

def extraer_url_imagen(cadena_completa):
    # Buscar el inicio de 'datathon/images/'
    inicio_datathon = cadena_completa.find('datathon/images/')
    if inicio_datathon != -1:
        # Extraer desde 'datathon/images/' en adelante
        return cadena_completa[inicio_datathon:]
    else:
        # Si 'datathon/images/' no se encuentra, devuelve la cadena original
        return cadena_completa

# Cargar los datos
data = cargar()

# dimensions of text-ada-embedding-002
d = 1536
faiss_index = faiss.IndexFlatL2(d)

vector_store = FaissVectorStore(faiss_index=faiss_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)


index = VectorStoreIndex.from_documents(
    data, storage_context=storage_context
)

# index = load_index_from_storage(storage_context)

# save index to disk
index.storage_context.persist()

# Crear la interfaz de Streamlit
st.title('¡Hola! 👋 Soy Elena, tu shopping Assistant, ¿qué quieres comprar hoy?')

user_query = st.text_input("Escribe aquí en qué te puedo ayudar, por ejemplo: ¿Qué sombrero me puedo poner con unos zapatos negros?", "¿Qué sombrero me puedo poner con unos zapatos negros?")

# Acción al presionar el botón de búsqueda
if st.button('Buscar'):

    response = pregunta(user_query)
    # Realizar la consulta con la entrada del usuario    

    # Mostrar los resultados de la consulta
    st.success(response)

    st.write('👉 Voy a buscar los mejores productos para ti.')

    sources, instrucciones, df = fuente(response, data)

    # st.write(f"Estoy buscando así {instrucciones}")

    # 37010684-CU, CU, CUERO, BROWN, Female, Adult, SHE, C-COMPLEMENTOS, Accesories, Swim and Intimate, Accessories, Footwear, Sandals, datathon/images/2022_37010684_CU.jpg
    # Separar la información
    # Expresión regular para encontrar la URL
    patron_url = r'datathon/images/\d{4}_\d{8}_\w{2}\.jpg'

    # Buscar la URL en la cadena
    url_encontrada = re.search(patron_url, sources)

    # Extraer la URL si se encuentra
    if url_encontrada:
        url = url_encontrada.group(0)
        print("URL encontrada:", url)
    else:
        print("URL no encontrada")

    st.image("images/" + url_encontrada)  # Asegúrate de que la ruta sea accesible
