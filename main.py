"""Command line entry point for Stellar One PDF security status reports."""

from __future__ import annotations

import argparse
import sys

from config import ConfigError, load_settings
from pdf_report import build_group_pdf_report, build_pdf_report
from stellar_api import StellarApiError, StellarOneClient, task_identifier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a PDF security status report for one TXOne Stellar One asset or one agent group."
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--agent-uuid", help="Stellar One agent UUID to report on.")
    target.add_argument("--agent-name", help="Hostname to resolve to an agent UUID.")
    target.add_argument("--agent-ip", help="IP address to resolve to an agent UUID.")
    group_target = parser.add_mutually_exclusive_group()
    group_target.add_argument("--group-uuid", help="Agent group UUID. Used alone, creates one report for all agents in the group.")
    group_target.add_argument("--group-name", help="Agent group name. Used alone, creates one report for all agents in the group.")
    parser.add_argument("--scan", action="store_true", help="Start a scan-now task before report generation.")
    parser.add_argument("--force-scan", action="store_true", help="Queue scan even when the target agent appears offline.")
    parser.add_argument("--no-wait", action="store_true", help="Do not wait for scan completion after starting a scan.")
    parser.add_argument("--output", required=True, help="Output PDF path, for example report.pdf.")
    parser.add_argument("--poll-seconds", type=int, default=5, help="Seconds between scan status checks.")
    parser.add_argument("--scan-timeout", type=int, default=300, help="Maximum seconds to wait for scan completion.")
    parser.add_argument("--stamp-image", help="Optional stamp image path to include in the report.")
    parser.add_argument("--signature-image", help="Optional signature image path to include in the report.")
    args = parser.parse_args()
    if not any((args.agent_uuid, args.agent_name, args.agent_ip, args.group_uuid, args.group_name)):
        parser.error("one of --agent-uuid, --agent-name, --agent-ip, --group-uuid, or --group-name is required")
    return args


def main() -> int:
    args = parse_args()

    try:
        settings = load_settings()
        client = StellarOneClient(settings)

        group_uuid = None
        group_context = None
        if args.group_uuid:
            group_uuid = args.group_uuid
            print(f"Using agent group UUID: {group_uuid}")
            group_context = client.get_group(group_uuid)
        elif args.group_name:
            print(f"Resolving agent group '{args.group_name}'...")
            group_uuid = client.find_group_uuid_by_name(args.group_name)
            print(f"Resolved group UUID: {group_uuid}")
            group_context = client.get_group(group_uuid)

        group_agents = client.list_group_agents(group_uuid) if group_uuid else None
        group_only_report = bool(group_uuid and not any((args.agent_uuid, args.agent_name, args.agent_ip)))

        if group_only_report:
            print(f"Fetching details for {len(group_agents or [])} agents in group...")
            agents = []
            policies = {}
            for index, group_agent in enumerate(group_agents or [], start=1):
                agent_uuid = str(group_agent.get("agentUuid") or "")
                if not agent_uuid:
                    continue
                label = group_agent.get("hostname") or agent_uuid
                print(f"  [{index}/{len(group_agents or [])}] {label}")
                try:
                    agent = client.get_agent(agent_uuid)
                except StellarApiError as exc:
                    agent = dict(group_agent)
                    agent["reportError"] = str(exc)
                agents.append(agent)

                try:
                    policies[agent_uuid] = client.get_agent_policy(agent_uuid)
                except StellarApiError as exc:
                    policies[agent_uuid] = {"error": str(exc)}

            scan_response = None
            scan_status = None
            if args.scan:
                online_count = sum(1 for agent in agents if agent.get("agentOnlineStatus") is True)
                offline_count = len(agents) - online_count
                if online_count == 0 and not args.force_scan:
                    print("All agents in the group appear offline; skipping scan. Use --force-scan to queue anyway.")
                    scan_response = {"skipped": True, "reason": "All agents in the group appeared offline before scan."}
                else:
                    if offline_count:
                        print(f"Warning: {offline_count} agent(s) appear offline; scan may not run on those agents.")
                    print("Starting scan-now task for group...")
                    scan_response = client.start_group_scan_now(group_uuid)
                    scan_task_id = task_identifier(scan_response)
                    if scan_task_id and not args.no_wait:
                        print(f"Waiting for scan task {scan_task_id} to finish...")
                        scan_status = client.wait_for_task(
                            scan_task_id,
                            poll_seconds=args.poll_seconds,
                            timeout_seconds=args.scan_timeout,
                        )
                        print("Scan task finished.")
                    elif scan_task_id:
                        print(f"Scan task {scan_task_id} started; not waiting because --no-wait was used.")

            print(f"Writing group PDF report to {args.output}...")
            build_group_pdf_report(
                args.output,
                group_context or {"groupUuid": group_uuid},
                agents,
                policies,
                scan_response,
                scan_status,
                stamp_image=args.stamp_image,
                signature_image=args.signature_image,
            )
            print(f"Report written to {args.output}")
            return 0

        if args.agent_uuid:
            agent_uuid = args.agent_uuid
            if group_uuid:
                client.ensure_agent_in_group(agent_uuid, group_uuid)
        elif args.agent_name:
            print(f"Resolving agent hostname '{args.agent_name}'...")
            agent_uuid = client.find_agent_uuid_by_name(args.agent_name, agents=group_agents)
            print(f"Resolved agent UUID: {agent_uuid}")
        elif args.agent_ip:
            print(f"Resolving agent IP '{args.agent_ip}'...")
            agent_uuid = client.find_agent_uuid_by_ip(args.agent_ip, agents=group_agents)
            print(f"Resolved agent UUID: {agent_uuid}")
        else:
            print(f"Resolving single agent in group '{group_uuid}'...")
            agent_uuid = client.resolve_single_agent_in_group(group_uuid)
            print(f"Resolved agent UUID: {agent_uuid}")

        print("Fetching agent details...")
        agent = client.get_agent(agent_uuid)
        print("Fetching agent policy...")
        policy = client.get_agent_policy(agent_uuid)

        scan_response = None
        scan_status = None
        if args.scan:
            if agent.get("agentOnlineStatus") is False and not args.force_scan:
                print("Agent appears offline; skipping scan. Use --force-scan to queue anyway.")
                scan_response = {"skipped": True, "reason": "Agent appeared offline before scan."}
            else:
                if agent.get("agentOnlineStatus") is False:
                    print("Warning: agent appears offline, but --force-scan was used.")
                print("Starting scan-now task...")
                scan_response = client.start_scan_now(agent_uuid, agent.get("productCode"))
                scan_task_id = task_identifier(scan_response)
                if scan_task_id and not args.no_wait:
                    print(f"Waiting for scan task {scan_task_id} to finish...")
                    scan_status = client.wait_for_task(
                        scan_task_id,
                        poll_seconds=args.poll_seconds,
                        timeout_seconds=args.scan_timeout,
                    )
                    print("Scan task finished.")
                elif scan_task_id:
                    print(f"Scan task {scan_task_id} started; not waiting because --no-wait was used.")
                else:
                    print("Scan request returned no task identifier; report will include the raw scan response.", file=sys.stderr)

        print(f"Writing PDF report to {args.output}...")
        build_pdf_report(
            args.output,
            agent,
            policy,
            scan_response,
            scan_status,
            stamp_image=args.stamp_image,
            signature_image=args.signature_image,
            group_context=group_context,
        )
        print(f"Report written to {args.output}")
        return 0
    except (ConfigError, StellarApiError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
