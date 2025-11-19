# web3_rpc_soundness

A small CLI tool to check the basic **soundness** of your Web3 setup by comparing multiple RPC endpoints side by side.  
It is conceptually inspired by ideas from **Aztec**, **Zama**, and **soundness-focused labs**: verify assumptions, avoid inconsistent views, and treat infrastructure as part of your security model.

The repository contains exactly two files:

- app.py
- README.md


## What it does

Given two or more Ethereum-compatible RPC URLs, the tool:

- Connects to each endpoint.
- Checks:
  - connectivity
  - chain ID
  - latest block number
  - basic latency
- Computes simple soundness notes:
  - do all endpoints agree on chain ID?
  - how far apart are their reported latest blocks?
  - are there any clearly lagging or offline endpoints?

This is a lightweight infrastructure check before you rely on multiple RPCs for a zk rollup, FHE-enabled app, or a soundness-critical protocol.


## Installation

Requirements:

- Python 3.10 or newer
- web3 Python package

Install dependency:

pip install web3

Place app.py and README.md into the root of your GitHub repository.


## Usage

Compare two or more endpoints:

python app.py --rpc https://mainnet.infura.io/v3/YOUR_KEY --rpc https://eth.llamarpc.com

Add a third endpoint with a longer timeout:

python app.py --rpc https://mainnet.infura.io/v3/YOUR_KEY --rpc https://eth.llamarpc.com --rpc https://rpc.ankr.com/eth --timeout 15

Get JSON output for monitoring systems:

python app.py --rpc https://mainnet.infura.io/v3/YOUR_KEY --rpc https://eth.llamarpc.com --json


## Example output (human-readable)

🔎 Web3 RPC Soundness Snapshot

[1] RPC 1
  RPC URL       : https://mainnet.infura.io/v3/...
  Status        : ✅ connected
  Chain ID      : 1
  Latest block  : 19500123
  Latency       : 112.45 ms

[2] RPC 2
  RPC URL       : https://eth.llamarpc.com
  Status        : ✅ connected
  Chain ID      : 1
  Latest block  : 19500124
  Latency       : 87.31 ms

--- Soundness notes ---
✅ All connected endpoints agree on chain ID.
ℹ️ Endpoints differ by up to 1 blocks, which is typically acceptable.


## JSON output structure

When using --json the tool prints an object with:

- endpoints: array of endpoint status objects
- notes: array of soundness notes

Each endpoint object contains:

- label
- rpc_url
- connected
- chain_id
- latest_block
- latency_ms
- error (if any)


## Relation to Aztec, Zama, and soundness

While this script does not directly interact with zk circuits or FHE, it focuses on the same principle: **soundness**.  
If your privacy or FHE-heavy system (Aztec-like, Zama-like, or formally verified) depends on multiple RPC providers, inconsistent views of the chain can undermine the integrity of your proofs or analyses.

Use this tool as a simple guardrail to check infrastructure assumptions before running critical Web3 workloads.
