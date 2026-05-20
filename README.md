# Stellar One Asset Security Status Report

Cross-platform Python CLI for macOS and Windows that generates a PDF security status report for one TXOne Stellar One asset using the Stellar One OpenAPI.

## Requirements

- Python 3.11+
- Stellar One API key

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add your API key:

```env
STELLAR_BASE_URL=https://stellar1-preview.txonedemo.com
STELLAR_API_KEY=your_api_key_here
STELLAR_VERIFY_SSL=true
```

Do not commit `.env` or API keys.

If a lab or demo Stellar One endpoint uses a certificate chain your local Python does not trust, prefer adding the issuing CA as a PEM file and setting:

```env
STELLAR_CA_BUNDLE=/path/to/company-or-demo-ca.pem
```

For temporary demo testing only, SSL certificate verification can be disabled:

```env
STELLAR_VERIFY_SSL=false
```

## Usage

Generate a report for a known agent UUID and run a scan first:

```bash
python main.py --agent-uuid <uuid> --scan --output report.pdf
```

Resolve an asset by hostname first:

```bash
python main.py --agent-name ST-WIN7-ENT-X64 --scan --output report.pdf
```

Resolve an asset by IP address:

```bash
python main.py --agent-ip 192.168.1.10 --output report.pdf
```

Resolve an asset inside an agent group:

```bash
python main.py --group-name "Production Line 1" --agent-name ST-WIN7-ENT-X64 --output report.pdf
```

Create one group report containing all agents in the group:

```bash
python main.py --group-name "Production Line 1" --output report.pdf
```

Start a scan but do not wait for it to finish:

```bash
python main.py --agent-name ST-WIN7-ENT-X64 --scan --no-wait --output report.pdf
```

Queue a scan even if the agent currently appears offline:

```bash
python main.py --agent-name ST-WIN7-ENT-X64 --scan --force-scan --output report.pdf
```

Include optional stamp and signature images:

```bash
python main.py --agent-name ST-WIN7-ENT-X64 --output report.pdf --stamp-image stamp.png --signature-image signature.png
```

Generate a report without starting a scan:

```bash
python main.py --agent-uuid <uuid> --output report.pdf
```

If the virtual environment is not activated, run the tool directly through the venv Python:

```bash
.venv/bin/python main.py --agent-name ST-WIN7-ENT-X64 --scan --output report.pdf
```

## Build An Exportable Python Package

Install the build tool:

```bash
.venv/bin/python -m pip install build
```

Build a wheel and source archive:

```bash
.venv/bin/python -m build
```

The exportable files will be created in `dist/`, for example:

```text
dist/stellar_one_asset_report-0.1.9-py3-none-any.whl
dist/stellar_one_asset_report-0.1.9.tar.gz
```

Install the wheel on another machine:

```bash
python3 -m pip install stellar_one_asset_report-0.1.9-py3-none-any.whl
```

After installation, run the CLI as:

```bash
stellar-report --agent-name ST-WIN7-ENT-X64 --scan --output report.pdf
```

The target machine still needs a `.env` file or equivalent environment variables with `STELLAR_BASE_URL` and `STELLAR_API_KEY`.

## Optional Standalone Executable

If you need a single executable for users who do not want to install Python, use PyInstaller on each target platform:

```bash
.venv/bin/python -m pip install pyinstaller
.venv/bin/python -m PyInstaller --onefile --name stellar-report main.py
```

The executable will be created under `dist/`. Build it separately on macOS and Windows.

For a compact English installation and use guide, see [INSTALL.md](INSTALL.md).

## What The Report Includes

1. Report metadata
2. Asset identity
3. Hardware inventory
4. Network information
5. Operating system and agent version
6. Agent status
7. Protection status
8. Scan execution result
9. Policy summary
10. Limitations

## Important Limitations

The report only uses data exposed by the configured Stellar One OpenAPI endpoints. It must not be interpreted as proof of:

- Vulnerability compliance
- Patch compliance
- Installed application inventory
- OS lifecycle or end-of-support status

Patch policy or component information may be shown when returned by the API, but the tool does not claim compliance from those fields.

## API Endpoints Used

- `GET /api/v1/agents`
- `GET /api/v1/agents/{agent_uuid}`
- `GET /api/v1/groups`
- `GET /api/v1/groups/{group_uuid}`
- `GET /api/v1/groups/{group_uuid}/agents`
- `POST /api/v1/task/scan-now`
- `GET /api/v1/task/{task_id_or_uuid}/status`
- `GET /api/v1/policy/agents/{agent_uuid}`
