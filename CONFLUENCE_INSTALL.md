# Stellar One Asset Report - Quick Guide

## Purpose

This CLI tool generates PDF security status reports from TXOne Stellar One OpenAPI.

It supports:

- One report for one asset
- One report for one agent group with all agents included
- Lookup by hostname, IP address, agent UUID, group name, or group UUID
- Optional scan-now task
- Optional stamp and signature images

## Install

Copy this file to the target machine:

```text
stellar_one_asset_report-0.1.9-py3-none-any.whl
```

### Windows

```powershell
py -3 -m pip install --upgrade stellar_one_asset_report-0.1.9-py3-none-any.whl
```

### macOS

```bash
python3 -m pip install --upgrade stellar_one_asset_report-0.1.9-py3-none-any.whl
```

## Configure

Create a file named `.env` in the same folder where you run the command.

Example:

```env
STELLAR_BASE_URL=https://your-stellar-one-url
STELLAR_API_KEY=your_api_key_here
STELLAR_VERIFY_SSL=true
```

For demo environments with certificate issues:

```env
STELLAR_VERIFY_SSL=false
```

Do not share the `.env` file. It contains the API key.

## Full Syntax

```bash
stellar-report [--agent-uuid <uuid> | --agent-name <hostname> | --agent-ip <ip-address>] \
  [--group-uuid <uuid> | --group-name <group-name>] \
  [--scan] [--force-scan] [--no-wait] \
  --output <report.pdf> \
  [--poll-seconds <seconds>] \
  [--scan-timeout <seconds>] \
  [--stamp-image <image-path>] \
  [--signature-image <image-path>]
```

## Common Examples

### Report For One Asset By Hostname

```bash
stellar-report --agent-name WIN7 --output WIN7.pdf
```

### Report For One Asset By IP Address

```bash
stellar-report --agent-ip 192.168.1.10 --output asset.pdf
```

### Report For One Asset By Agent UUID

```bash
stellar-report --agent-uuid <uuid> --output asset.pdf
```

### Report For One Group

This creates one PDF containing all agents in the group.

```bash
stellar-report --group-name "Production Line 1" --output group-report.pdf
```

### Report For One Asset Inside A Group

```bash
stellar-report --group-name "Production Line 1" --agent-name WIN7 --output WIN7.pdf
```

### Start Scan And Do Not Wait

```bash
stellar-report --agent-name WIN7 --scan --no-wait --output WIN7.pdf
```

By default, scans are skipped when a single target agent appears offline. To queue anyway:

```bash
stellar-report --agent-name WIN7 --scan --force-scan --output WIN7.pdf
```

### Group Report With Scan

```bash
stellar-report --group-name "Production Line 1" --scan --no-wait --output group-report.pdf
```

### Add Stamp And Signature Images

```bash
stellar-report --agent-name WIN7 --output WIN7.pdf --stamp-image stamp.png --signature-image signature.png
```

## Output

The PDF is saved in the folder where the command is run, unless a full output path is provided.

Example:

```bash
stellar-report --agent-name WIN7 --output C:\Reports\WIN7.pdf
```

## Troubleshooting

### Missing Configuration

Error:

```text
Missing STELLAR_BASE_URL
```

Fix:

- Check that `.env` exists in the same folder where the command is run.
- Check that `STELLAR_BASE_URL` and `STELLAR_API_KEY` are set.

### Certificate Error

For demo environments, set:

```env
STELLAR_VERIFY_SSL=false
```

### Command Not Found

Restart the terminal after installation, or reinstall:

```bash
python3 -m pip install --upgrade stellar_one_asset_report-0.1.9-py3-none-any.whl
```

On Windows:

```powershell
py -3 -m pip install --upgrade stellar_one_asset_report-0.1.9-py3-none-any.whl
```

## Report Limitations

The report does not claim:

- Vulnerability compliance
- Patch compliance
- Installed application inventory
- Operating system lifecycle status

The report only includes data available from Stellar One OpenAPI.
