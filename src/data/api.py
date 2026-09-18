from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Dict, Any
import uvicorn
from pydantic import BaseModel

# Import repository functions
from .repository import (
    get_all_projects,
    get_project,
    get_projects_by_state,
    get_projects_by_sector,
    get_projects_by_ministry,
    get_project_history
)

app = FastAPI(
    title="InfraGuard-AI PAIMANA API",
    description="API for accessing cleaned and engineered PAIMANA project data.",
    version="1.0.0"
)

@app.get("/api/projects", response_model=List[Dict[str, Any]])
def list_projects(state: Optional[str] = None, sector: Optional[str] = None, ministry: Optional[str] = None):
    if state:
        df = get_projects_by_state(state)
    elif sector:
        df = get_projects_by_sector(sector)
    elif ministry:
        df = get_projects_by_ministry(ministry)
    else:
        df = get_all_projects()
        
    return df.to_dict('records')

@app.get("/api/projects/{project_code}", response_model=Dict[str, Any])
def get_project_details(project_code: str):
    project = get_project(project_code)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.get("/api/projects/{project_code}/history", response_model=List[Dict[str, Any]])
def get_project_history_data(project_code: str):
    df = get_project_history(project_code)
    if df.empty:
        raise HTTPException(status_code=404, detail="History not found for this project")
    return df.to_dict('records')

if __name__ == "__main__":
    print("Starting FastAPI server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=5175)
