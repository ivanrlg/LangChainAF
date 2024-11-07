# Building a Chatbot with Azure Functions and LangChain

![image-5](https://github.com/user-attachments/assets/493e9870-ba2c-4879-b96e-f945b128fc20)


## Introduction

This project guides you through creating a serverless, scalable chatbot using Azure Functions and LangChain. Leveraging Azure Functions alongside LangChain for language model support, this application performs tasks such as document processing, querying, and response generation using OpenAI’s embeddings model and Pinecone for vector storage.

For additional details, please refer to the original blog post on WordPress: [Building a Chatbot with Azure Functions and LangChain: A Comprehensive Guide](https://ivansingleton.dev/creating-an-intelligent-assistant-with-azure-functions-and-langchain-part-i/).

## Prerequisites

To run this project, ensure you have:

- An Azure account with access to Azure Functions.
- Basic knowledge of Python.
- API keys for OpenAI and Pinecone.
- Access to the GitHub repository: LangChainBot.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ivanrlg/LangChainAF.git
   cd LangChainAF
   ```

2. **Configure Environment Variables**

   Create a `local.settings.json` file to securely store environment variables:

   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
       "AzureWebJobsStorage": "UseDevelopmentStorage=true",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "OPENAI_API_KEY": "your_openai_api_key",
       "PINECONE_API_KEY": "your_pinecone_api_key",
       "PINECONE_ENVIRONMENT": "your_pinecone_environment"
     }
   }
   ```

   **Important:** Keep your API keys secure and avoid exposing them in public repositories.

3. **Install Dependencies**

   Install the required libraries using the `requirements.txt` file:

   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

- **Azure Functions**:
  - `process_document`: Processes and indexes documents by generating embeddings and storing them in Pinecone.
  - `get_answer`: Generates answers to user queries by retrieving relevant documents and using OpenAI's language model to produce a response.
- **LangChain Orchestration**:
  - **Document Loader**, **Text Splitter**, **Embeddings**, **Vector Store**, and **Retriever** modules streamline document processing and retrieval.
- **Pinecone Vector DB**:
  - Stores vectorized embeddings for efficient similarity searches.
- **OpenAI GPT Models**:
  - Used to generate human-like responses based on the context retrieved from documents.

## Usage

1. **Run the Azure Function Locally**

   Start the Azure Function app locally for testing:

   ```bash
   func start
   ```

2. **Endpoints**

   - **Process Document Endpoint**
     - **Function**: `process_document`
     - **Method**: `POST`
     - **URL**: `http://localhost:7071/api/process_document`
     - **Body**: Raw text content of the document to process.
     - **Headers**: Set `Content-Type` to `text/plain`.
     - **Example Request**:

       ```bash
       curl -X POST "http://localhost:7071/api/process_document" \
       -H "Content-Type: text/plain" \
       --data-binary "@path/to/your/document.txt"
       ```

     - **Example Response**:

       ```json
       {
         "status": "success",
         "chunks_processed": 5
       }
       ```
   - **Get Answer Endpoint**
     - **Function**: `get_answer`
     - **Method**: `POST`
     - **URL**: `http://localhost:7071/api/get_answer`
     - **Body** (raw JSON):

       ```json
       {
         "query": "How do I process a sales order?",
         "system_prompt": "You are a helpful assistant."
       }
       ```

       - **Parameters**:
         - `query`: The user's question or query.
         - `system_prompt` (optional): A custom system prompt to guide the assistant's behavior.

     - **Example Response**:

       ```json
       {
         "answer": "To process a sales order, you should...",
         "context": "Relevant context from documents...",
         "similar_docs": [
           {
             "content": "Document content 1",
             "score": 0.85
           },
           {
             "content": "Document content 2",
             "score": 0.80
           }
         ]
       }
       ```

## Code Overview

- **`function_app.py`**: Main file that defines the Azure Functions for processing, searching, and generating answers. Implements document splitting, embedding generation, vector storage, and interaction with OpenAI's GPT models.

- **Key Functions**:

  1. **`initialize_embeddings`**: Sets up the OpenAI Embeddings model using the API key.

  2. **`get_pinecone_client`**: Initializes the Pinecone client to interact with the vector database.

  3. **`process_document`**: Splits the uploaded document into chunks, generates embeddings, and stores them in Pinecone.

  4. **`search_documents`**: Queries the vector database to find documents similar to the provided query.

  5. **`get_answer`**: Combines the functionality of searching for relevant documents and generating a coherent answer using OpenAI's GPT model. It retrieves similar documents, constructs a prompt including the context, and generates an answer.

## How `get_answer` Works

1. **Receive User Query**: Accepts a user's question and an optional system prompt.

2. **Retrieve Relevant Documents**: Uses `similarity_search_with_score` to find documents that are similar to the query.

3. **Construct Context**: Builds a context string by concatenating the content of the retrieved documents.

4. **Prepare Prompt for OpenAI**: Creates a list of messages to send to the OpenAI ChatCompletion API, including the system prompt, the user's query, and the context.

5. **Generate Answer**: Calls the OpenAI API to generate an answer based on the prompt and context.

6. **Return Response**: Sends back the generated answer, the context used, and the similar documents found.

## Testing the Application

Using Postman, curl, or a similar tool, you can test all the endpoints:

- **Process Documents**:
  - Ensure you have documents to process.
  - Send a POST request to `process_document` with the document content.

- **Get Answer**:
  - After processing documents, use the `get_answer` endpoint.
  - Provide a query relevant to the processed documents.
  - Verify that the response includes an answer that utilizes the context.

## Notes

- **Indexing Before Asking Questions**: Ensure that you've processed and indexed documents using the `process_document` endpoint before attempting to get answers.

- **Error Handling**: The functions contain error handling to manage issues like missing content, invalid JSON, or API errors.

- **OpenAI API Key Usage**: Be mindful of your OpenAI API usage and monitor for any rate limits or quota restrictions.

- **Model Selection**: The `get_answer` function uses the `gpt-4` model. Ensure you have access to this model or adjust to `gpt-3.5-turbo` if necessary.

## Additional Resources

- [LangChain Documentation](https://github.com/langchain-ai/langchain)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Azure Functions Python Developer Guide](https://docs.microsoft.com/azure/azure-functions/functions-reference-python)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference/introduction)
- [Understanding Embeddings in Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/tutorials/ai-cookbook/rag-overview)
- [Retrieval-Augmented Generation (RAG) Explained](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/tutorials/ai-cookbook/rag-overview)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Final Remarks

- **Ensure Environment Variables Are Set**: The `OPENAI_API_KEY` and `PINECONE_API_KEY` are essential for the application to function. Double-check that

 these are correctly set in your environment or `local.settings.json`.

- **Security Considerations**: Avoid committing your API keys or sensitive information to version control. Use environment variables or secure key vaults when deploying to production.

- **Scaling and Performance**: Azure Functions can scale to meet demand, but be mindful of potential costs associated with OpenAI API usage and Pinecone queries.
