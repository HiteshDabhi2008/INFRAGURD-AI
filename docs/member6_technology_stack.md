# Technology Stack (Member 6)

This document outlines the proposed open-source technology stack for building the InfraGuard-AI platform. The stack is designed for rapid prototyping during the Hackathon while remaining scalable.

## Frontend & Dashboard Application
- **Framework**: **Streamlit** (Python)
  - *Why*: Allows rapid creation of data-heavy interactive dashboards and integrates natively with Python-based ML and Data Engineering pipelines. Avoids the need to build a separate React/Vue frontend for Day 2 prototypes.
- **Visualizations**: **Plotly** / **Seaborn**
  - *Why*: Plotly provides highly interactive, web-ready charts (hover, zoom, pan) which are vastly superior to static Matplotlib charts for a dashboard.

## Backend & Database
- **Database**: **Supabase** (PostgreSQL)
  - *Why*: Open-source Firebase alternative. Provides a robust relational database to store the `paimana_master_v1.csv` and the final ML predictions, along with instant REST/GraphQL APIs.
- *(Optional)* **FastAPI**: If we need to decouple the ML inference engine from the Streamlit frontend.

## AI & Machine Learning
- **Predictive ML Models**: **XGBoost** / **Scikit-Learn**
  - *Why*: Members 3 and 4 will output trained XGBoost models. These will be pickled (`.pkl`) and loaded into the backend.
- **LLM Engine**: **Groq API** or **Hugging Face Inference API**
  - *Why*: Groq provides ultra-low latency inference for models like LLaMA 3. Hugging Face provides access to thousands of open-source models.
- **Agent Framework**: **LangChain**
  - *Why*: Handles tool calling (fetching SQL data) and RAG routing natively.

## RAG (Retrieval-Augmented Generation)
- **Vector Database**: **ChromaDB** or **FAISS**
  - *Why*: Open-source, runs locally, perfect for embedding the PAIMANA data dictionaries and docs.
- **Embeddings**: **sentence-transformers**
  - *Why*: High quality, local, free text embedding generation.

## Day-2 Minimum Viable Product (MVP) Stack
For the Day-2 MVP, we will simplify the stack to ensure we can deliver a working prototype:
- **Streamlit** (Frontend, Dashboard, and Chat UI)
- **Pandas / Local CSV** (Acting as the Database temporarily before moving to Supabase)
- **Pickled XGBoost Models** (For live risk scoring)
- **LangChain + Groq API** (For the AI Assistant)
- **FAISS** (For document retrieval)
