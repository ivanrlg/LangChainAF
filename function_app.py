import azure.functions as func
import logging
import json
import os
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone as PineconeVectorStore
from langchain.docstore.document import Document
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from openai import OpenAI

app = func.FunctionApp()

def initialize_embeddings():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_api_key
    )
    return embeddings

def get_pinecone_client():
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY not found in environment variables")
    pc = PineconeClient(api_key=pinecone_api_key)
    return pc

@app.route(route="process_document", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def process_document(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Process Document function processed a request.')

    try:
        # Get content from request
        content = req.get_body().decode('utf-8')
        logging.info('Content received: %s', content[:100])

        if not content:
            return func.HttpResponse(
                "No content received",
                status_code=400
            )

        # Configure text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        # Split text into chunks
        texts = text_splitter.split_text(content)

        # Create documents
        docs = [
            Document(
                page_content=t,
                metadata={
                    "chunk_index": i,
                    "upload_date": str(datetime.now())
                }
            )
            for i, t in enumerate(texts)
        ]

        # Initialize embeddings and Pinecone
        embeddings = initialize_embeddings()
        pc = get_pinecone_client()
        index_name = "langchain"

        # Check if index exists
        existing_indexes = pc.list_indexes()
        if index_name not in [idx.name for idx in existing_indexes.indexes]:
            pc.create_index(
                name=index_name,
                dimension=embeddings.embedding_dim,
                metric="cosine",
                pod_type="s1.x1",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

        # Connect to index
        index = pc.Index(index_name)

        # Insert documents
        vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            text_key="text"
        )

        vector_store.add_documents(docs)

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "chunks_processed": len(docs)
            }),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error processing document: {str(e)}")
        error_details = {
            "error": str(e),
            "type": str(type(e).__name__),
            "trace": str(e.__traceback__)
        }
        return func.HttpResponse(
            json.dumps(error_details),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="get_answer", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def get_answer(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Get Answer function processed a request.')

    try:
        req_body = req.get_json()
        query = req_body.get('query')
        system_prompt = req_body.get('system_prompt', 'You are an AI assistant.')

        if not query:
            return func.HttpResponse(
                json.dumps({"error": "No query provided"}),
                status_code=400,
                mimetype="application/json"
            )

        # Search for similar documents
        embeddings = initialize_embeddings()
        pc = get_pinecone_client()
        index_name = "langchain"
        index = pc.Index(index_name)
        vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            text_key="text"
        )

        results = vector_store.similarity_search_with_score(query, k=3)
        filtered_results = [(doc, score) for doc, score in results if score > 0.7]

        if not filtered_results:
            return func.HttpResponse(
                json.dumps({
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "metadata": {
                        "query": query,
                        "documents_found": len(results)
                    }
                }),
                mimetype="application/json"
            )

        # Build context
        context = "\n\n".join([doc.page_content for doc, score in filtered_results])

        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]

        # Get OpenAI response
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.2,
            max_tokens=800
        )

        answer = response.choices[0].message.content.strip()

        return func.HttpResponse(
            json.dumps({
                "answer": answer,
                "context": context,
                "similar_docs": [
                    {
                        "content": doc.page_content,
                        "score": float(score)
                    } for doc, score in filtered_results
                ]
            }),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error generating answer: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )