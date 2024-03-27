from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader

from qdrant_client import QdrantClient
from qdrant_client.http import models
from subir_archivo import RUTA

CLOUD=''
CLOUD_COLLECTION='test_collection'
KEY=''
LOCAL='http://localhost:6333'
LOCAL_COLLECTION='vector_db'


def subir_archivo_qdrant(filename,drive_id):
    print('qdrant_funciones.subir_archivo_qdrant()')
    print('subiendo')
    #get extension
    filename_split=filename.split('.')
    print('extension ',filename_split)
    if len(filename_split)>1:
        print('comprobando extension')
        if filename_split[1]=='pdf':
            loader = PyPDFLoader(RUTA+'drive_tracker/'+filename)
        elif filename_split[1] in ['txt', 'md','csv','html','py','js','css']:
            loader = TextLoader(RUTA+'drive_tracker/'+filename)
        else:
            print('extension sin implementar')
            return False
        #load document
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                    chunk_overlap=50)
        texts = text_splitter.split_documents(documents)
        #add normal filename(without route) as an extra metadata key by iterating trough the texts list
        for text in texts:
            text.metadata['filename'] = filename
            text.metadata['drive_id'] = drive_id
        # Load the embedding model 
        model_name = "BAAI/bge-large-en"
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': False}
        embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        #print('embeddings: ',embeddings )
        print(len(texts))
        print('conectando a qdrant')
        try:
            url = "http://localhost:6333"
            print(Qdrant.from_documents(
                texts,
                embeddings,
                url=CLOUD,
                api_key=KEY,
                prefer_grpc=False,
                collection_name=CLOUD_COLLECTION,
                force_recreate=True,
            ))
            print('archivo subido')
        except Exception as error:
            print('error al subir archivo: ',error)
            return False
        return True
    print('archivo sin extension')
    return False

def borrar_archivo_qdrant(filename):
    print('qdrant_funciones.borrar_archivo_qdrant()')
    #search embeddings with the filename as metadata
    print('conectando a qdrant')
    try:
        client = QdrantClient(url=CLOUD,api_key=KEY)#QdrantClient(host='localhost', port=6333,)
        embeddings=client.scroll(
            collection_name=CLOUD_COLLECTION,limit=1000, 
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.filename",
                        match=models.MatchValue(value=filename),
                    ),
                ]
            ),
        )
        print('hay ',(len(embeddings[0])),' embeddings')
        #print(embeddings)
        if len(embeddings[0])==0:
            print('no hay nada que borrar')
            return False
        point_ids=[e.id for e in embeddings[0]]
        #print('borrando: ', point_ids)
        client.delete(
            collection_name=CLOUD_COLLECTION,
            points_selector=models.PointIdsList(
                points=point_ids,
            ),
        )
        print('archivo borrado')
        return True
    except Exception as error:
        print('error al subir archivo: ',error)
        return False




#borrar_archivo_qdrant('titanic.csv')
#subir_archivo_qdrant('README.md')
