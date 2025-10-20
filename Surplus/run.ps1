
Param([int]$Port=5000)
Set-Location $PSScriptRoot
if (!(Test-Path ".\.venv")) { py -3 -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:FLASK_SECRET_KEY = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$env:PORT = $Port
python app.py
