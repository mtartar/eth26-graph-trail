"""tx_hash -> block explorer URL construction, per chain."""

_EXPLORER_TX_URL_TEMPLATES: dict[str, str] = {
    "ethereum": "https://etherscan.io/tx/{tx_hash}",
    "base": "https://basescan.org/tx/{tx_hash}",
}


def build_explorer_url(chain: str, tx_hash: str) -> str:
    """Build the block-explorer transaction URL for a given chain and tx hash."""
    template = _EXPLORER_TX_URL_TEMPLATES.get(chain.lower())
    if template is None:
        raise ValueError(f"No block explorer configured for chain '{chain}'")
    return template.format(tx_hash=tx_hash)
