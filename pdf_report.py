"""PDF report generation for one Stellar One asset."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def build_pdf_report(
    output_path: str,
    agent: dict[str, Any],
    policy: dict[str, Any] | None,
    scan_response: dict[str, Any] | None,
    scan_status: dict[str, Any] | None,
    stamp_image: str | None = None,
    signature_image: str | None = None,
    group_context: dict[str, Any] | None = None,
) -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="TXOne Stellar One Security Status Report",
    )

    styles = _styles()
    story: list[Any] = [
        Paragraph("TXOne Stellar One Security Status Report", styles["Title"]),
        Paragraph("by Christian Søgaard Nielsen", styles["Subtitle"]),
        Paragraph("Licensed for private and commercial use.", styles["Subtitle"]),
        Paragraph("Single asset status report generated from Stellar One OpenAPI data.", styles["BodyText"]),
        Spacer(1, 8 * mm),
    ]

    story.extend(_summary_block(agent, scan_response, scan_status, styles))
    story.extend(_approval_block(stamp_image, signature_image, styles))

    sections = [
        ("1. Report Metadata", _metadata_rows(agent, group_context)),
        ("2. Asset Identity", _asset_identity_rows(agent)),
        ("3. Hardware Inventory", _hardware_inventory_rows(agent)),
        ("4. Network Information", _network_rows(agent)),
        ("5. Operating System and Agent Version", _os_agent_rows(agent)),
        ("6. Agent Status", _agent_status_rows(agent)),
        ("7. Protection Status", _protection_rows(agent)),
        ("8. Scan Execution Result", _scan_rows(scan_response, scan_status)),
        ("9. Policy Summary", _policy_rows(policy)),
        ("10. Limitations", _limitations_rows()),
    ]

    for title, rows in sections:
        story.extend(_section(title, rows, styles))

    doc.build(story)


def build_group_pdf_report(
    output_path: str,
    group: dict[str, Any],
    agents: list[dict[str, Any]],
    policies: dict[str, dict[str, Any]] | None,
    scan_response: dict[str, Any] | None,
    scan_status: dict[str, Any] | None,
    stamp_image: str | None = None,
    signature_image: str | None = None,
) -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="TXOne Stellar One Group Security Status Report",
    )

    styles = _styles()
    story: list[Any] = [
        Paragraph("TXOne Stellar One Group Security Status Report", styles["Title"]),
        Paragraph("by Christian Søgaard Nielsen", styles["Subtitle"]),
        Paragraph("Licensed for private and commercial use.", styles["Subtitle"]),
        Paragraph("Group asset status report generated from Stellar One OpenAPI data.", styles["BodyText"]),
        Spacer(1, 6 * mm),
    ]

    story.extend(_group_summary_block(group, agents, scan_response, scan_status, styles))
    story.extend(_approval_block(stamp_image, signature_image, styles))
    story.extend(_group_hardware_inventory_section(agents, styles))
    story.extend(_group_inventory_section(agents, policies or {}, styles))
    story.extend(_group_agent_details_sections(agents, policies or {}, styles))
    story.extend(_section("Limitations", _limitations_rows(), styles))

    doc.build(story)


def _styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    styles["Title"].fontName = "Helvetica-Bold"
    styles["Title"].fontSize = 20
    styles["Title"].leading = 24
    styles["Title"].textColor = colors.HexColor("#15324A")

    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#52616B"),
        )
    )

    styles["Heading2"].fontName = "Helvetica-Bold"
    styles["Heading2"].fontSize = 12
    styles["Heading2"].leading = 15
    styles["Heading2"].spaceBefore = 8
    styles["Heading2"].textColor = colors.HexColor("#15324A")

    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12

    styles.add(
        ParagraphStyle(
            name="Cell",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            name="Key",
            parent=styles["Cell"],
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#34495E"),
        )
    )
    return styles


def _section(title: str, rows: list[tuple[str, Any]], styles: dict[str, ParagraphStyle]) -> list[Any]:
    table_rows = [
        [Paragraph(str(key), styles["Key"]), Paragraph(_format_value(value), styles["Cell"])]
        for key, value in rows
    ]
    table = Table(table_rows, colWidths=[55 * mm, 116 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F6F8")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E1E8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [KeepTogether([Paragraph(title, styles["Heading2"]), table]), Spacer(1, 5 * mm)]


def _summary_block(
    agent: dict[str, Any],
    scan_response: dict[str, Any] | None,
    scan_status: dict[str, Any] | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    summary_rows = [
        ("Asset", agent.get("hostname")),
        ("Overall status", _overall_status(agent, scan_status)),
        ("Agent online", agent.get("agentOnlineStatus")),
        ("Realtime scan", agent.get("realtimeScanStatus")),
        ("Lockdown", agent.get("lockdownStatus")),
        ("Device control", agent.get("deviceControlStatus")),
        ("Component status", agent.get("componentStatus")),
        ("Scan status", _short_scan_status(scan_response, scan_status)),
        ("Key limitation", "No vulnerability, patch compliance, application inventory, or OS lifecycle claim is made."),
    ]
    return _section("Executive Summary", summary_rows, styles)


def _group_summary_block(
    group: dict[str, Any],
    agents: list[dict[str, Any]],
    scan_response: dict[str, Any] | None,
    scan_status: dict[str, Any] | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    online_count = sum(1 for agent in agents if agent.get("agentOnlineStatus") is True)
    attention_count = sum(1 for agent in agents if _agent_needs_attention(agent))
    rows = [
        ("Agent group", group.get("name")),
        ("Agent group UUID", group.get("groupUuid")),
        ("Agents included", len(agents)),
        ("Agents online", f"{online_count} of {len(agents)}"),
        ("Agents needing attention", attention_count),
        ("Scan status", _short_scan_status(scan_response, scan_status)),
        ("Key limitation", "No vulnerability, patch compliance, application inventory, or OS lifecycle claim is made."),
    ]
    return _section("Executive Summary", rows, styles)


def _group_inventory_section(
    agents: list[dict[str, Any]],
    policies: dict[str, dict[str, Any]],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    headers = ["Hostname", "IP", "OS", "Version", "Online", "Realtime", "Lockdown", "Device", "Policy"]
    rows = [[Paragraph(header, styles["Key"]) for header in headers]]
    for agent in agents:
        agent_uuid = str(agent.get("agentUuid") or "")
        policy_type, _ = _policy_payload(policies.get(agent_uuid, {}))
        values = [
            agent.get("hostname"),
            agent.get("ipAddress"),
            agent.get("os"),
            agent.get("productVersion"),
            agent.get("agentOnlineStatus"),
            agent.get("realtimeScanStatus"),
            agent.get("lockdownStatus"),
            agent.get("deviceControlStatus"),
            policy_type,
        ]
        rows.append([Paragraph(_format_value(value), styles["Cell"]) for value in values])

    table = Table(
        rows,
        colWidths=[34 * mm, 28 * mm, 48 * mm, 28 * mm, 17 * mm, 35 * mm, 30 * mm, 30 * mm, 24 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F6F8")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E1E8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return [Paragraph("Agent Inventory", styles["Heading2"]), table, Spacer(1, 5 * mm)]


def _group_hardware_inventory_section(
    agents: list[dict[str, Any]],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    headers = ["Hostname", "SMBIOS UUID", "Baseboard Serial", "Memory", "Volumes"]
    rows = [[Paragraph(header, styles["Key"]) for header in headers]]
    for agent in agents:
        identity = _nested(agent, "sysInfoExtra", "identity")
        values = [
            agent.get("hostname"),
            identity.get("smbiosUuid"),
            identity.get("baseboardSerialNumber"),
            _memory_summary(agent),
            _volumes_summary(agent),
        ]
        rows.append([Paragraph(_format_value(value), styles["Cell"]) for value in values])

    table = Table(
        rows,
        colWidths=[35 * mm, 55 * mm, 48 * mm, 40 * mm, 96 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F6F8")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E1E8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return [Paragraph("Hardware Inventory", styles["Heading2"]), table, Spacer(1, 5 * mm)]


def _group_agent_details_sections(
    agents: list[dict[str, Any]],
    policies: dict[str, dict[str, Any]],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    story: list[Any] = [Paragraph("Agent Details", styles["Heading2"])]
    for agent in agents:
        title = agent.get("hostname") or agent.get("agentUuid") or "Unknown Agent"
        agent_uuid = str(agent.get("agentUuid") or "")
        policy_type, policy_body = _policy_payload(policies.get(agent_uuid, {}))
        rows = [
            ("Hostname", agent.get("hostname")),
            ("Agent UUID", agent.get("agentUuid")),
            ("IP address", agent.get("ipAddress")),
            ("MAC address", agent.get("macAddress")),
            ("Operating system", agent.get("os")),
            ("Agent version", agent.get("productVersion")),
            ("Online", agent.get("agentOnlineStatus")),
            ("Activated", agent.get("activated")),
            ("Realtime scan", agent.get("realtimeScanStatus")),
            ("Lockdown", agent.get("lockdownStatus")),
            ("Device control", agent.get("deviceControlStatus")),
            ("Component status", agent.get("componentStatus")),
            ("Reboot required", agent.get("rebootRequired")),
            ("Policy type", policy_type),
            ("Policy summary", _summarize_dict(policy_body) if isinstance(policy_body, dict) else policy_body),
            ("Retrieval warning", agent.get("reportError")),
        ]
        story.extend(_section(str(title), rows, styles))
    return story


def _approval_block(
    stamp_image: str | None,
    signature_image: str | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    left_items: list[Any] = [Paragraph("Stamp", styles["Key"])]
    right_items: list[Any] = [Paragraph("Signature", styles["Key"])]

    if stamp_image:
        left_items.append(_scaled_image(stamp_image, width=42 * mm, height=24 * mm))
    else:
        left_items.append(Spacer(1, 18 * mm))
        left_items.append(Paragraph("_" * 26, styles["Cell"]))

    if signature_image:
        right_items.append(_scaled_image(signature_image, width=55 * mm, height=24 * mm))
    else:
        right_items.append(Spacer(1, 18 * mm))
        right_items.append(Paragraph("_" * 34, styles["Cell"]))

    signature_line = Table(
        [
            [
                left_items,
                right_items,
                [
                    Paragraph("Prepared by", styles["Key"]),
                    Paragraph("Christian Søgaard Nielsen", styles["Cell"]),
                    Paragraph(datetime.now(timezone.utc).strftime("%Y-%m-%d"), styles["Cell"]),
                ],
            ]
        ],
        colWidths=[50 * mm, 62 * mm, 59 * mm],
        hAlign="LEFT",
    )
    signature_line.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E1E8")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBFCFD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [KeepTogether([Paragraph("Approval", styles["Heading2"]), signature_line]), Spacer(1, 5 * mm)]


def _metadata_rows(
    agent: dict[str, Any],
    group_context: dict[str, Any] | None = None,
) -> list[tuple[str, Any]]:
    rows = [
        ("Generated at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Data source", "TXOne Stellar One OpenAPI"),
        ("Report scope", "One Stellar One asset"),
        ("Asset UUID", agent.get("agentUuid")),
    ]
    if group_context:
        rows.extend(
            [
                ("Agent group", group_context.get("name")),
                ("Agent group UUID", group_context.get("groupUuid")),
            ]
        )
    return rows


def _asset_identity_rows(agent: dict[str, Any]) -> list[tuple[str, Any]]:
    identity = _nested(agent, "sysInfoExtra", "identity")
    return [
        ("Hostname", agent.get("hostname")),
        ("Agent UUID", agent.get("agentUuid")),
        ("Agent ID", agent.get("agentId")),
        ("Product code", agent.get("productCode")),
        ("Vendor", agent.get("vendor")),
        ("Model", agent.get("model")),
        ("Location", agent.get("location")),
        ("Description", agent.get("description")),
        ("SMBIOS UUID", identity.get("smbiosUuid")),
        ("Baseboard serial", identity.get("baseboardSerialNumber")),
    ]


def _hardware_inventory_rows(agent: dict[str, Any]) -> list[tuple[str, Any]]:
    identity = _nested(agent, "sysInfoExtra", "identity")
    sys_info_extra = agent.get("sysInfoExtra")
    extra_keys = []
    if isinstance(sys_info_extra, dict):
        extra_keys = sorted(key for key in sys_info_extra if key not in {"identity", "mem", "volumes"})

    rows = [
        ("SMBIOS UUID", identity.get("smbiosUuid")),
        ("Baseboard serial", identity.get("baseboardSerialNumber")),
        ("Total memory", _memory_value(agent, "totalMemory")),
        ("Free memory", _memory_value(agent, "freeMemory")),
        ("Volumes", _volumes_summary(agent)),
    ]

    for key in extra_keys:
        rows.append((_humanize(key), sys_info_extra.get(key)))
    return rows


def _network_rows(agent: dict[str, Any]) -> list[tuple[str, Any]]:
    return [
        ("IP address", agent.get("ipAddress")),
        ("MAC address", agent.get("macAddress")),
        ("Communication port", agent.get("commPort")),
        ("NAT mode", agent.get("natMode")),
        ("Last connected", _timestamp(agent.get("connectedAt"))),
        ("Time gap", agent.get("timeGap")),
    ]


def _os_agent_rows(agent: dict[str, Any]) -> list[tuple[str, Any]]:
    components = _components(agent)
    return [
        ("Operating system", agent.get("os")),
        ("Agent version", agent.get("productVersion")),
        ("Agent edition", agent.get("agentEdition")),
        ("Language code", agent.get("language")),
        ("Last upgraded", _timestamp(agent.get("upgradedAt"))),
        ("Scan components", components),
    ]


def _agent_status_rows(agent: dict[str, Any]) -> list[tuple[str, Any]]:
    return [
        ("Online", agent.get("agentOnlineStatus")),
        ("Activated", agent.get("activated")),
        ("Management status", agent.get("managementStatus")),
        ("Sync status", agent.get("syncStatus")),
        ("Sync interval", agent.get("syncInterval")),
        ("Policy inheritance", agent.get("policyInheritance")),
        ("Policy version", agent.get("policyVersion")),
        ("License status", agent.get("licenseStatus")),
        ("License type", agent.get("licenseType")),
        ("License expiry", _timestamp(agent.get("licenseExpiredAt"))),
        ("Reboot required", agent.get("rebootRequired")),
    ]


def _protection_rows(agent: dict[str, Any]) -> list[tuple[str, Any]]:
    protections = agent.get("protection")
    if isinstance(protections, list):
        protection_text = ", ".join(_humanize(item) for item in protections) or "No protection flags returned"
    else:
        protection_text = protections

    return [
        ("Protection flags", protection_text),
        ("Realtime scan status", agent.get("realtimeScanStatus")),
        ("Lockdown status", agent.get("lockdownStatus")),
        ("Device control status", agent.get("deviceControlStatus")),
        ("Component status", agent.get("componentStatus")),
        ("Maintenance status", agent.get("maintenanceStatus")),
        ("Maintenance start", _timestamp(agent.get("maintenanceStartAt"))),
        ("Maintenance end", _timestamp(agent.get("maintenanceEndAt"))),
        ("Approved list state", agent.get("approvedListState")),
        ("Approved list count", agent.get("approvedListCount")),
        ("Approved list updated", _timestamp(agent.get("approvedListUpdatedAt"))),
    ]


def _scan_rows(
    scan_response: dict[str, Any] | None,
    scan_status: dict[str, Any] | None,
) -> list[tuple[str, Any]]:
    if not scan_response:
        return [
            ("Scan requested", "No"),
            ("Result", "Scan was not requested for this report run."),
        ]
    if scan_response.get("skipped"):
        return [
            ("Scan requested", "Yes"),
            ("Scan executed", "No"),
            ("Reason", scan_response.get("reason")),
        ]

    tasks = scan_status.get("tasks", []) if scan_status else []
    task_summary = []
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            continue
        task_summary.append(
            " / ".join(
                _humanize(task.get(field))
                for field in ("taskType", "taskStatus", "taskResult")
                if task.get(field)
            )
        )

    return [
        ("Scan requested", "Yes"),
        ("Windows task ID", scan_response.get("protectTaskId")),
        ("Windows-Legacy task UUID", scan_response.get("protectLegacyModeTaskUuid")),
        ("Task status", "\n".join(task_summary) if task_summary else "No task status returned"),
    ]


def _overall_status(agent: dict[str, Any], scan_status: dict[str, Any] | None) -> str:
    findings = []
    if agent.get("agentOnlineStatus") is False:
        findings.append("agent offline")
    if agent.get("activated") is False:
        findings.append("agent not activated")
    if agent.get("rebootRequired") is True:
        findings.append("reboot required")
    if _scan_has_failure(scan_status):
        findings.append("scan task reported failure")

    if findings:
        return "Attention recommended: " + ", ".join(findings)
    return "No immediate issue indicated by returned asset status fields"


def _agent_needs_attention(agent: dict[str, Any]) -> bool:
    return any(
        (
            agent.get("agentOnlineStatus") is False,
            agent.get("activated") is False,
            agent.get("rebootRequired") is True,
            bool(agent.get("reportError")),
        )
    )


def _short_scan_status(
    scan_response: dict[str, Any] | None,
    scan_status: dict[str, Any] | None,
) -> str:
    if not scan_response:
        return "Scan not requested"
    if scan_response.get("skipped"):
        return f"Scan skipped: {scan_response.get('reason')}"
    if not scan_status:
        return "Scan requested; completion status not included"
    tasks = scan_status.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        return "Scan status not returned"
    return "; ".join(
        " / ".join(
            _humanize(task.get(field))
            for field in ("taskStatus", "taskResult")
            if isinstance(task, dict) and task.get(field)
        )
        for task in tasks
        if isinstance(task, dict)
    )


def _scan_has_failure(scan_status: dict[str, Any] | None) -> bool:
    if not scan_status:
        return False
    tasks = scan_status.get("tasks", [])
    if not isinstance(tasks, list):
        return False
    for task in tasks:
        if not isinstance(task, dict):
            continue
        result = str(task.get("taskResult", ""))
        if result and "FAIL" in result:
            return True
    return False


def _scaled_image(path: str, width: float, height: float) -> Image:
    image = Image(path)
    image._restrictSize(width, height)
    return image


def _policy_rows(policy: dict[str, Any] | None) -> list[tuple[str, Any]]:
    if not policy:
        return [("Policy", "Policy data was not retrieved.")]

    policy_type, policy_body = _policy_payload(policy)
    if not isinstance(policy_body, dict):
        return [("Policy type", policy_type), ("Policy", "No policy body returned.")]

    rows: list[tuple[str, Any]] = [("Policy type", policy_type)]
    for key in sorted(policy_body):
        value = policy_body.get(key)
        if isinstance(value, dict):
            rows.append((_humanize(key), _summarize_dict(value)))
        elif value is not None:
            rows.append((_humanize(key), value))
    return rows or [("Policy", "No policy settings returned.")]


def _limitations_rows() -> list[tuple[str, Any]]:
    return [
        ("Vulnerability compliance", "Not assessed. This API response does not expose vulnerability compliance data."),
        ("Patch compliance", "Not assessed. Patch policy/configuration may be visible, but compliance state is not established by this report."),
        ("Installed application inventory", "Not assessed. The report does not claim a full installed application inventory."),
        ("OS lifecycle status", "Not assessed. The API response does not expose vendor support lifecycle status."),
        ("Report meaning", "This report reflects Stellar One asset, protection, scan task, and policy data available at generation time."),
    ]


def _policy_payload(policy: dict[str, Any]) -> tuple[str, Any]:
    for key in ("spPolicy", "splmPolicy", "linuxPolicy"):
        if key in policy:
            return key, policy.get(key)
    return "unknown", policy


def _components(agent: dict[str, Any]) -> str:
    product_block = agent.get("protect") or agent.get("protectLegacy") or {}
    components = product_block.get("scanComponents") if isinstance(product_block, dict) else None
    if not isinstance(components, list) or not components:
        return "Not returned"
    labels = []
    for component in components:
        if isinstance(component, dict):
            name = component.get("name", "Unknown")
            version = component.get("version", "unknown version")
            labels.append(f"{name} {version}")
    return "\n".join(labels) if labels else "Not returned"


def _memory_summary(agent: dict[str, Any]) -> str:
    total_memory = _memory_value(agent, "totalMemory")
    free_memory = _memory_value(agent, "freeMemory")
    if total_memory == "Not returned" and free_memory == "Not returned":
        return "Not returned"
    return f"Total: {total_memory}\nFree: {free_memory}"


def _memory_value(agent: dict[str, Any], key: str) -> str:
    mem = _nested(agent, "sysInfoExtra", "mem")
    return _bytes_value(mem.get(key))


def _volumes_summary(agent: dict[str, Any]) -> str:
    volumes = _nested_list(agent, "sysInfoExtra", "volumes")
    if not volumes:
        return "Not returned"

    labels = []
    for volume in volumes:
        if not isinstance(volume, dict):
            continue
        drive = volume.get("drive") or "Unknown drive"
        volume_type = volume.get("type") or f"Drive type {volume.get('driveType')}"
        total = _bytes_value(volume.get("total"))
        free = _bytes_value(volume.get("free"))
        labels.append(f"{drive} ({volume_type}) total {total}, free {free}")
    return "\n".join(labels) if labels else "Not returned"


def _summarize_dict(value: dict[str, Any]) -> str:
    parts = []
    for key, item in value.items():
        if isinstance(item, (dict, list)):
            parts.append(f"{_humanize(key)}: returned")
        else:
            parts.append(f"{_humanize(key)}: {_format_value(item)}")
    return "\n".join(parts) if parts else "Returned, but empty"


def _nested(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def _nested_list(payload: dict[str, Any], *keys: str) -> list[Any]:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return []
        current = current.get(key)
    return current if isinstance(current, list) else []


def _bytes_value(value: Any) -> str:
    if value in (None, ""):
        return "Not returned"
    try:
        size = int(value)
    except (TypeError, ValueError):
        return str(value)

    units = ["B", "KB", "MB", "GB", "TB"]
    amount = float(size)
    for unit in units:
        if abs(amount) < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(amount)} {unit}"
            return f"{amount:.1f} {unit}"
        amount /= 1024


def _timestamp(value: Any) -> str:
    if value in (None, "", 0, "0"):
        return "Not returned"
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return str(value)

    if timestamp > 10_000_000_000:
        timestamp = timestamp // 1000
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (OSError, OverflowError, ValueError):
        return f"Returned value: {value}"


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return "Not returned"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return "\n".join(_format_value(item) for item in value) if value else "None returned"
    if isinstance(value, dict):
        return _summarize_dict(value)
    return _humanize(value)


def _humanize(value: Any) -> str:
    text = str(value)
    for prefix in (
        "PROTECTION_",
        "TASK_STATUS_",
        "TASK_RESULT_",
        "TASK_TYPE_",
        "COMPONENT_STATUS_",
        "DEVICE_CONTROL_STATUS_",
    ):
        text = text.removeprefix(prefix)
    return text.replace("_", " ").strip().title()
