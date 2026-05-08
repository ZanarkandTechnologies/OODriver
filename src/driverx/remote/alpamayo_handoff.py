"""Secret-safe Alpamayo handoff manifests for remote/Kasm inference."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AlpamayoHandoffManifest:
    package_path: str
    package_sha256: str
    cache_key: str
    output_root: str
    safe_for_kasm_proxy: bool = True

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "package_path": self.package_path,
            "package_sha256": self.package_sha256,
            "cache_key": self.cache_key,
            "output_root": self.output_root,
            "safe_for_kasm_proxy": self.safe_for_kasm_proxy,
            "notes": [
                "No credentials are embedded in this handoff manifest.",
                "Install HF credentials through Kasm web terminal or a direct safe channel.",
            ],
        }


def package_sha256(package_path: Path) -> str:
    return hashlib.sha256(package_path.expanduser().read_bytes()).hexdigest()


def package_cache_key(package_path: Path, *, mode: str = "alpamayo") -> str:
    return hashlib.sha256(f"{mode}:{package_sha256(package_path)}".encode("utf-8")).hexdigest()[:24]


def build_alpamayo_handoff_manifest(package_path: Path, output_root: Path, *, mode: str = "remote-kasm") -> AlpamayoHandoffManifest:
    expanded = package_path.expanduser()
    digest = package_sha256(expanded)
    return AlpamayoHandoffManifest(
        package_path=str(expanded),
        package_sha256=digest,
        cache_key=hashlib.sha256(f"{mode}:{digest}".encode("utf-8")).hexdigest()[:24],
        output_root=str(output_root),
    )


def write_alpamayo_handoff_manifest(run_dir: Path, manifest: AlpamayoHandoffManifest) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "alpamayo_handoff_manifest.json"
    path.write_text(json.dumps(manifest.to_jsonable(), indent=2), encoding="utf-8")
    return path


__all__ = [
    "AlpamayoHandoffManifest",
    "build_alpamayo_handoff_manifest",
    "package_cache_key",
    "package_sha256",
    "write_alpamayo_handoff_manifest",
]
