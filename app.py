#!/usr/bin/env python3
import argparse
import sys
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from web3 import Web3


@dataclass
class RpcStatus:
    label: str
    rpc_url: str
    connected: bool
    chain_id: int | None
    latest_block: int | None
    latency_ms: float | None
    error: str | None


def check_rpc(label: str, rpc_url: str, timeout: int) -> RpcStatus:
    t0 = time.time()
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": timeout}))
    except Exception as exc:
        return RpcStatus(
            label=label,
            rpc_url=rpc_url,
            connected=False,
            chain_id=None,
            latest_block=None,
            latency_ms=None,
            error=f"provider error: {exc}",
        )

    if not w3.is_connected():
        return RpcStatus(
            label=label,
            rpc_url=rpc_url,
            connected=False,
            chain_id=None,
            latest_block=None,
            latency_ms=None,
            error="not connected",
        )

    try:
        chain_id = w3.eth.chain_id
        latest_block = w3.eth.block_number
    except Exception as exc:
        elapsed = (time.time() - t0) * 1000
        return RpcStatus(
            label=label,
            rpc_url=rpc_url,
            connected=False,
            chain_id=None,
            latest_block=None,
            latency_ms=elapsed,
            error=f"RPC call failed: {exc}",
        )

    elapsed = (time.time() - t0) * 1000
    return RpcStatus(
        label=label,
        rpc_url=rpc_url,
        connected=True,
        chain_id=int(chain_id),
        latest_block=int(latest_block),
        latency_ms=elapsed,
        error=None,
    )


def summarize_soundness(statuses: List[RpcStatus]) -> List[str]:
    notes: List[str] = []

    connected = [s for s in statuses if s.connected]
    if len(connected) < 2:
        notes.append("Not enough connected endpoints to assess consistency.")
        return notes

    # Compare chain IDs
    chain_ids = {s.chain_id for s in connected}
    if len(chain_ids) > 1:
        notes.append("⚠️ Different chain IDs across endpoints; RPC mix may be unsafe.")
    else:
        notes.append("✅ All connected endpoints agree on chain ID.")

    # Compare latest blocks
    blocks = [s.latest_block for s in connected if s.latest_block is not None]
    if not blocks:
        notes.append("No block information available from connected endpoints.")
        return notes

    max_block = max(blocks)
    min_block = min(blocks)
    diff = max_block - min_block

    if diff == 0:
        notes.append("✅ All connected endpoints are at the same latest block.")
    elif diff <= 2:
        notes.append(f"ℹ️ Endpoints differ by up to {diff} blocks, which is typically acceptable.")
    else:
        notes.append(f"⚠️ Endpoints differ by {diff} blocks; consider removing lagging RPCs.")

    return notes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="web3_rpc_soundness",
        description=(
            "Compare multiple Web3 RPC endpoints for basic soundness: "
            "chain ID agreement, block height alignment, and latency."
        ),
    )
    parser.add_argument(
        "--rpc",
        action="append",
        required=True,
        help="HTTP RPC URL (can be passed multiple times).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Per-endpoint timeout in seconds (default: 10).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of human-readable text.",
    )
    return parser.parse_args()


def print_human(statuses: List[RpcStatus], notes: List[str]) -> None:
    print("🔎 Web3 RPC Soundness Snapshot")
    print("")
    for idx, s in enumerate(statuses, start=1):
        print(f"[{idx}] {s.label}")
        print(f"  RPC URL       : {s.rpc_url}")
        if not s.connected:
            print(f"  Status        : ❌ offline ({s.error})")
            print("")
            continue
        print("  Status        : ✅ connected")
        print(f"  Chain ID      : {s.chain_id}")
        print(f"  Latest block  : {s.latest_block}")
        print(f"  Latency       : {s.latency_ms:.2f} ms")
        print("")
    print("--- Soundness notes ---")
    for n in notes:
        print(n)


def main() -> int:
    args = parse_args()

    if len(args.rpc) < 2:
        print("You must provide at least two --rpc endpoints to compare.", file=sys.stderr)
        return 1

    statuses: List[RpcStatus] = []
    for idx, url in enumerate(args.rpc, start=1):
        label = f"RPC {idx}"
        statuses.append(check_rpc(label, url, args.timeout))

    notes = summarize_soundness(statuses)

    if args.json:
        import json

        payload: Dict[str, Any] = {
            "endpoints": [asdict(s) for s in statuses],
            "notes": notes,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(statuses, notes)

    # Non-zero exit if any warning-level note is present
    has_warning = any(n.startswith("⚠️") for n in notes)
    return 2 if has_warning else 0


if __name__ == "__main__":
    raise SystemExit(main())
