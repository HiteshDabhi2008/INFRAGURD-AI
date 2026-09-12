# RAG Architecture (Member 6)

This document details the Retrieval-Augmented Generation (RAG) architecture for the InfraGuard-AI platform. The RAG system is responsible for allowing the AI Assistant to answer unstructured, qualitative queries based on MoSPI reports, guidelines, and project documents.

## RAG Pipeline Flow

### 1. Ingestion Phase (Offline)
1. **Document Source**: MoSPI PAIMANA PDFs, Data Dictionaries (`docs/data_dictionary.md`), EDA Reports, and external policy documents.
2. **Parsing**: Use `pdfplumber` or `PyPDF2` to extract raw text from binary documents.
3. **Chunking**: Split the text into semantic chunks (e.g., 500-1000 tokens) using LangChain's `RecursiveCharacterTextSplitter`. Overlap chunks (e.g., 100 tokens) to preserve context across boundaries.
4. **Embedding**: Convert the text chunks into dense vector representations using a model like `sentence-transformers/all-MiniLM-L6-v2` (from Hugging Face).
5. **Vector Store**: Insert the embeddings and metadata (source file, page number) into a vector database (FAISS or ChromaDB).

### 2. Retrieval Phase (Online/Runtime)
1. **User Query**: User asks: "What is the definition of a Mega Project according to MoSPI?"
2. **Query Embedding**: The same Hugging Face model converts the user's natural language query into a vector.
3. **Similarity Search**: The Vector Store (FAISS/ChromaDB) performs a Cosine Similarity search to find the Top-K (e.g., 3) most relevant document chunks.
4. **Context Injection**: The retrieved chunks are injected into the LLM Prompt.

### 3. Generation Phase
- **Prompt Structure**:
  ```text
  You are the PAIMANA AI Assistant. Answer the user's question using ONLY the provided context. If the answer is not in the context, say "I cannot find this information in the official documents."
  
  CONTEXT:
  {retrieved_chunks}
  
  USER QUESTION: {user_query}
  ```
- **Output**: LLM generates the response and appends the source citations (e.g., *Source: data_dictionary.md, Line 45*).

## Strict Grounding Rule
The LLM must be strictly prompted to avoid hallucination. It should never rely on its pre-trained parametric memory to invent project rules, MoSPI definitions, or infrastructure costs. If the vector store returns no relevant context, the LLM must gracefully fallback.
