$ErrorActionPreference = 'Stop'

python src/generate_synthetic_data.py --mode sample
python src/run_pipeline.py
node src/build_dashboard.mjs
python src/build_report.py

Write-Host 'Project outputs are ready under outputs/, dashboard/, and report/.'
