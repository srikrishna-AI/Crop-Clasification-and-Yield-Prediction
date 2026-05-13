# TODO

- [x] Update `render.yaml` to set Render Python `runtimeVersion` to Python 3.10 for backend and frontend
- [x] Update `render.yaml` buildCommand to use `pip install --only-binary=:all:` to force wheel installs (avoid pandas source build)
- [ ] Re-deploy to Render and confirm build succeeds
- [ ] Quick runtime sanity check: backend `/` and Streamlit-triggered `/recomendCrop` and `/yieldPrediction`

