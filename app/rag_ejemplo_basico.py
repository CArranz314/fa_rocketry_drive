from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from qdrant_client import QdrantClient
from qdrant_funciones import CLOUD,CLOUD_COLLECTION, KEY
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

openai_apikey=''

async def retrieve_docs(query:str):
    client = QdrantClient(
        url=CLOUD, prefer_grpc=False, api_key=KEY
    )
    
    model_name = "BAAI/bge-large-en"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    db = Qdrant(client=client, embeddings=embeddings, collection_name=CLOUD_COLLECTION)

    docs = db.similarity_search_with_score(query=query, k=5)
    response={}
    for num,i in enumerate(docs):
        doc, score = i
        response[num]={"score": score, "content": doc.page_content, "metadata": doc.metadata}
    
    prompt = PromptTemplate(
    template="Con el siguiente contexto, responde a la pregunta. Contexto: {response} Pregunta a responder: {query}",
    input_variables=["response","query"],
    )
    print(prompt.format(response=response,query=query))
    llm = ChatOpenAI(openai_api_key=openai_apikey, model="gpt-4")
    mensaje=llm.invoke(prompt.format(response=response,query=query))
    response["mensaje"]=mensaje
    return response
