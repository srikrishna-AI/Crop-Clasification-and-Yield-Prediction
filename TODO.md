- [ ] Update src/ui_app.py to use API_BASE_URL for backend calls (done for recomendCrop/yieldPrediction)
- [x] Update render.yaml to deploy backend (FastAPI) as one Render web service
- [x] Update render.yaml to deploy frontend (Streamlit) as another Render web service

- [x] Ensure backend startCommand points to src/app.py and proper module path
- [x] Ensure frontend startCommand runs streamlit from src/ui_app.py
- [x] Set Streamlit environment variable API_BASE_URL to backend service URL
- [ ] Local sanity check: run FastAPI and Streamlit and verify API calls
- [ ] Attempt Render deploy and confirm both services come up

