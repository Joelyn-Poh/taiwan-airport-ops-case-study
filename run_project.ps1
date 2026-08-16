$ErrorActionPreference = 'Stop'

python src/generate_synthetic_data.py --mode sample
python src/run_pipeline.py
node src/build_dashboard.mjs

Write-Host 'Project outputs are ready under outputs/ and dashboard/.'
