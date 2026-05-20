# Stellar One Asset Report - Installation and Use

## Purpose

Stellar One Asset Report is a small cross-platform Python CLI tool for generating a PDF security status report for one TXOne Stellar One asset.

The tool connects to Stellar One OpenAPI, reads asset and policy status, optionally starts a scan-now task, and writes a clean PDF report.

## Typical Use Cases

- Create a point-in-time security status report for a single Stellar One asset.
- Document agent identity, network information, operating system, agent status, protection status, and assigned policy.
- Run a scan-now task before report generation and include the scan task result when available.
- Produce a customer, PoC, or internal handover artifact without exposing API keys in source code.

## Important Limitations

The report only contains data exposed by the configured Stellar One OpenAPI endpoints.

It does not claim:

- Vulnerability compliance
- Patch compliance
- Installed application inventory
- Operating system lifecycle or end-of-support status

## Requirements

- Python 3.11 or newer
- Network access to Stellar One
- A Stellar One API key

## Install From Wheel

Copy the `.whl` file from the `dist/` folder to the target machine.

Install it with pip:

```bash
python3 -m pip install stellar_one_asset_report-0.1.9-py3-none-any.whl
```

On Windows, use:

```powershell
py -3 -m pip install stellar_one_asset_report-0.1.9-py3-none-any.whl
```

## Configuration

Create a `.env` file in the folder where you run the command:

```env
STELLAR_BASE_URL=https://stellar1-preview.txonedemo.com
STELLAR_API_KEY=your_api_key_here
STELLAR_VERIFY_SSL=true
STELLAR_CA_BUNDLE=
```

For lab or demo environments where the certificate chain is not trusted by local Python, you can temporarily use:

```env
STELLAR_VERIFY_SSL=false
```

For production or customer use, prefer a trusted certificate chain or set `STELLAR_CA_BUNDLE` to a PEM file.

## Generate A Report

Using an agent UUID:

```bash
stellar-report --agent-uuid <uuid> --scan --output report.pdf
```

Using a hostname:

```bash
stellar-report --agent-name ST-WIN7-ENT-X64 --scan --output report.pdf
```

Using an IP address:

```bash
stellar-report --agent-ip 192.168.1.10 --output report.pdf
```

Using an agent group as a filter:

```bash
stellar-report --group-name "Production Line 1" --agent-ip 192.168.1.10 --output report.pdf
```

Create one group report containing all agents in the group:

```bash
stellar-report --group-name "Production Line 1" --output report.pdf
```

Start a scan but do not wait for it to finish:

```bash
stellar-report --agent-name ST-WIN7-ENT-X64 --scan --no-wait --output report.pdf
```

By default, scans are skipped when a single target agent appears offline. To queue the scan anyway:

```bash
stellar-report --agent-name ST-WIN7-ENT-X64 --scan --force-scan --output report.pdf
```

Generate a report without starting a scan:

```bash
stellar-report --agent-name ST-WIN7-ENT-X64 --output report.pdf
```

Include a stamp and signature image:

```bash
stellar-report --agent-name ST-WIN7-ENT-X64 --output report.pdf --stamp-image stamp.png --signature-image signature.png
```

Supported image formats depend on your local ReportLab/Pillow installation, but PNG and JPG are normally safe choices.

## Output

If `--output report.pdf` is used, the report is written to the current working directory.

You can also provide an absolute path:

```bash
stellar-report --agent-name ST-WIN7-ENT-X64 --output "/Users/example/Desktop/report.pdf"
```

## Build From Source

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install build
python -m build
```

The package files will be created in:

```text
dist/
```

## License Notice In Report

Generated reports include:

```text
by Christian Søgaard Nielsen
Licensed for private and commercial use.
```
