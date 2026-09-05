 Pakistan Construction Cost Calculator

An interactive Flask web application built from the supplied parametric cost-calculator notebook. It estimates residential construction costs in PKR for 5, 10, 15, and 20 marla plots across major Pakistani cities.

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ADMIN_PASSWORD="set-a-strong-password"
python app.py
```
Visit `http://127.0.0.1:5000`. The administrator panel is at `/admin/login`.

## Admin controls
The admin can update material prices, labour, contractor rates, city/soil/quality factors, plot rules, and insulation rates through a protected configuration editor. Rates save to `data/rates.json` and immediately affect all new calculations.

Default local admin password: `change-me-2026`. Always set `ADMIN_PASSWORD` before deployment.

## Disclaimer
All figures are estimates based on Pakistani 2026-market research and contractor-pricing assumptions. Confirm quotations, specifications, and approvals with qualified local professionals before committing to work.
