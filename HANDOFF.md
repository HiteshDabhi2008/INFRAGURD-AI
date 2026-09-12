# Day 1 Handoff (From Member 6)

This document outlines exactly what Member 6 (Dashboard & AI Assistant) requires from the rest of the InfraGuard-AI team for Day 2 execution.

## To Member 1 (Data Engineer)
- **Requirement**: I need the final `paimana_master_v1.csv` to be extremely clean.
- Ensure all numerical columns (Cost, Expenditure, Progress) are strictly numeric types (no string commas or mixed types), as Streamlit/Pandas will crash if it tries to plot strings.
- Please provide the final `docs/data_dictionary.md` so I can chunk it into the RAG Vector DB.

## To Members 3 & 4 (ML Engineers)
- **Requirement**: Once you train your final Day-2 ML models, save them as `.pkl` (pickle) or `.joblib` files.
- Provide a short python inference script or function that takes a row of project data and outputs the `cost_overrun_probability` and `time_overrun_probability`. The Streamlit dashboard will call this function live.
- If you use SHAP for explainability, please provide a function that generates the SHAP plot object so I can embed it directly into the Streamlit UI.

## To Member 5 (Risk Engine)
- **Requirement**: Please provide the final scoring script that combines Member 3 & 4's probabilities into the final `LOW / MEDIUM / HIGH / CRITICAL` buckets.
- Please provide a `dict` or mapping of the "Early Warning Rules" (e.g., `rule_1: "High Expenditure, Low Progress"`). The AI Assistant will use these string definitions to explain to the user *why* a project is failing.

## What Member 6 Will Build on Day 2
- A complete, interactive **Streamlit Dashboard** hosting the KPI cards, interactive Plotly charts, and the High-Risk Project datatable.
- A functional **PAIMANA AI Assistant** sidebar using LangChain and Groq.
- A **FAISS Vector Store** containing the Data Dictionary and methodology docs for the LLM to use via RAG.
