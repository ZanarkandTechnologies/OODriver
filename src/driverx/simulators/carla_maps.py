"""Install and probe CARLA AdditionalMaps packages."""

from __future__ import annotations

import importlib
import json
import os
import shutil
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from driverx.core.config import read_config_mapping


DEFAULT_CARLA_VERSION = "0.9.16"
DEFAULT_DESIRED_MAPS = ("Town13",)
DEFAULT_CACHE_DIR = Path("artifacts/cache/carla")
DEFAULT_REQUIRED_FREE_BYTES = 16 * 1024 * 1024 * 1024


@dataclass(frozen=True)
class CarlaInstallCandidate:
    path: Path
    source: str
    platform: str
    exists: bool
    writable: bool
    executable_path: Path | None
    confidence: int
    notes: tuple[str, ...] = ()

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "source": self.source,
            "platform": self.platform,
            "exists": self.exists,
            "writable": self.writable,
            "executable_path": str(self.executable_path) if self.executable_path else None,
            "confidence": self.confidence,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class CarlaMapsInstallConfig:
    version: str = DEFAULT_CARLA_VERSION
    platform: str = "auto"
    carla_root: Path | None = None
    package_url: str | None = None
    package_path: Path | None = None
    package_cache_dir: Path = DEFAULT_CACHE_DIR
    desired_maps: tuple[str, ...] = DEFAULT_DESIRED_MAPS
    search_paths: tuple[Path, ...] = ()
    dry_run: bool = False
    required_free_bytes: int = DEFAULT_REQUIRED_FREE_BYTES


@dataclass(frozen=True)
class CarlaMapsInstallResult:
    status: str
    dry_run: bool
    version: str
    platform: str
    carla_root: Path | None
    package_url: str | None
    package_path: Path | None
    package_size_bytes: int | None
    disk_free_bytes: int | None
    required_free_bytes: int
    desired_maps: tuple[str, ...]
    candidates: tuple[CarlaInstallCandidate, ...]
    archive_members_sample: tuple[str, ...]
    extracted_count: int
    map_markers: dict[str, list[str]]
    blockers: tuple[str, ...]
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "dry_run": self.dry_run,
            "version": self.version,
            "platform": self.platform,
            "carla_root": str(self.carla_root) if self.carla_root else None,
            "package_url": self.package_url,
            "package_path": str(self.package_path) if self.package_path else None,
            "package_size_bytes": self.package_size_bytes,
            "disk_free_bytes": self.disk_free_bytes,
            "required_free_bytes": self.required_free_bytes,
            "desired_maps": list(self.desired_maps),
            "candidates": [candidate.to_jsonable() for candidate in self.candidates],
            "archive_members_sample": list(self.archive_members_sample),
            "extracted_count": self.extracted_count,
            "map_markers": self.map_markers,
            "blockers": list(self.blockers),
            "error": self.error,
        }


@dataclass(frozen=True)
class CarlaMapLoadAttempt:
    map_name: str
    success: bool
    loaded_map: str | None
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "map_name": self.map_name,
            "success": self.success,
            "loaded_map": self.loaded_map,
            "error": self.error,
        }


@dataclass(frozen=True)
class CarlaMapProbeConfig:
    host: str = "127.0.0.1"
    port: int = 2000
    timeout_s: float = 20.0
    desired_maps: tuple[str, ...] = DEFAULT_DESIRED_MAPS
    attempt_load: bool = True


@dataclass(frozen=True)
class CarlaMapInventory:
    connected: bool
    host: str
    port: int
    server_version: str | None
    client_version: str | None
    current_map: str | None
    available_maps: tuple[str, ...]
    load_attempts: tuple[CarlaMapLoadAttempt, ...]
    error: str | None = None

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "server_version": self.server_version,
            "client_version": self.client_version,
            "current_map": self.current_map,
            "available_maps": list(self.available_maps),
            "load_attempts": [attempt.to_jsonable() for attempt in self.load_attempts],
            "error": self.error,
        }


def load_carla_maps_install_config(
    path: Path,
    *,
    dry_run: bool | None = None,
) -> CarlaMapsInstallConfig:
    raw = read_config_mapping(path)
    maps_raw = raw.get("carla_maps", raw)
    if not isinstance(maps_raw, dict):
        raise ValueError("Config field 'carla_maps' must be a mapping.")
    return CarlaMapsInstallConfig(
        version=str(maps_raw.get("version", DEFAULT_CARLA_VERSION)),
        platform=str(maps_raw.get("platform", "auto")),
        carla_root=_maybe_path(maps_raw.get("carla_root")),
        package_url=_maybe_str(maps_raw.get("package_url")),
        package_path=_maybe_path(maps_raw.get("package_path")),
        package_cache_dir=_maybe_path(maps_raw.get("package_cache_dir"))
        or DEFAULT_CACHE_DIR,
        desired_maps=_split_csv(maps_raw.get("desired_maps"), DEFAULT_DESIRED_MAPS),
        search_paths=_split_paths(maps_raw.get("search_paths")),
        dry_run=bool(maps_raw.get("dry_run", False)) if dry_run is None else dry_run,
        required_free_bytes=int(
            maps_raw.get("required_free_bytes", DEFAULT_REQUIRED_FREE_BYTES)
            or DEFAULT_REQUIRED_FREE_BYTES
        ),
    )


def load_carla_map_probe_config(path: Path) -> CarlaMapProbeConfig:
    raw = read_config_mapping(path)
    maps_raw = raw.get("carla_maps", raw)
    if not isinstance(maps_raw, dict):
        raise ValueError("Config field 'carla_maps' must be a mapping.")
    return CarlaMapProbeConfig(
        host=str(maps_raw.get("host", "127.0.0.1")),
        port=int(maps_raw.get("port", 2000) or 2000),
        timeout_s=float(maps_raw.get("timeout_s", 20.0) or 20.0),
        desired_maps=_split_csv(maps_raw.get("desired_maps"), DEFAULT_DESIRED_MAPS),
        attempt_load=bool(maps_raw.get("attempt_load", True)),
    )


def discover_carla_install_candidates(
    search_paths: Iterable[Path] | None = None,
) -> list[CarlaInstallCandidate]:
    """Discover likely CARLA package roots without mutating anything."""

    roots = _default_search_paths()
    if search_paths is not None:
        roots.extend(_expand_path(path) for path in search_paths)

    seen: set[Path] = set()
    candidates: list[CarlaInstallCandidate] = []
    for raw_root in roots:
        root = raw_root.expanduser()
        if root in seen:
            continue
        seen.add(root)
        candidates.extend(_candidates_for_path(root))

    unique: dict[Path, CarlaInstallCandidate] = {}
    for candidate in candidates:
        previous = unique.get(candidate.path)
        if previous is None or candidate.confidence > previous.confidence:
            unique[candidate.path] = candidate
    return sorted(
        unique.values(),
        key=lambda candidate: (candidate.confidence, candidate.writable, str(candidate.path)),
        reverse=True,
    )


def install_carla_additional_maps(
    config: CarlaMapsInstallConfig,
) -> CarlaMapsInstallResult:
    candidates = tuple(discover_carla_install_candidates(config.search_paths))
    carla_root = _resolve_carla_root(config.carla_root, candidates)
    platform = _resolve_platform(config.platform, carla_root)
    package_url = config.package_url or default_additional_maps_url(
        config.version,
        platform,
    )
    package_path = config.package_path or _default_package_path(
        config.package_cache_dir,
        config.version,
        platform,
    )
    package_size = _local_file_size(package_path) or _remote_file_size(package_url)
    disk_free = _disk_free(carla_root or package_path.parent)
    required_free = _required_free_bytes(package_size, config.required_free_bytes)
    blockers = _install_preflight_blockers(
        carla_root=carla_root,
        package_path=package_path,
        disk_free=disk_free,
        required_free=required_free,
    )
    if config.dry_run:
        return CarlaMapsInstallResult(
            status="dry_run" if not blockers else "blocked",
            dry_run=True,
            version=config.version,
            platform=platform,
            carla_root=carla_root,
            package_url=package_url,
            package_path=package_path,
            package_size_bytes=package_size,
            disk_free_bytes=disk_free,
            required_free_bytes=required_free,
            desired_maps=config.desired_maps,
            candidates=candidates,
            archive_members_sample=(),
            extracted_count=0,
            map_markers=_find_map_markers(carla_root, config.desired_maps),
            blockers=tuple(blockers),
        )
    if blockers:
        return CarlaMapsInstallResult(
            status="blocked",
            dry_run=False,
            version=config.version,
            platform=platform,
            carla_root=carla_root,
            package_url=package_url,
            package_path=package_path,
            package_size_bytes=package_size,
            disk_free_bytes=disk_free,
            required_free_bytes=required_free,
            desired_maps=config.desired_maps,
            candidates=candidates,
            archive_members_sample=(),
            extracted_count=0,
            map_markers=_find_map_markers(carla_root, config.desired_maps),
            blockers=tuple(blockers),
        )

    assert carla_root is not None
    try:
        if not package_path.exists():
            package_path.parent.mkdir(parents=True, exist_ok=True)
            _download_file(package_url, package_path)
        package_size = _local_file_size(package_path)
        archive_sample = tuple(_archive_members_sample(package_path, limit=20))
        extracted_count = _extract_archive(package_path, carla_root)
        marker_path = carla_root / "Import" / f"{package_path.name}.done"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(
            f"Installed by DriverX from {package_url}\n",
            encoding="utf-8",
        )
        markers = _find_map_markers(carla_root, config.desired_maps)
        missing_maps = [name for name, paths in markers.items() if not paths]
        result_blockers = (
            tuple(f"No extracted marker found for desired map: {name}" for name in missing_maps)
            if missing_maps
            else ()
        )
        return CarlaMapsInstallResult(
            status="installed" if not result_blockers else "installed_with_warnings",
            dry_run=False,
            version=config.version,
            platform=platform,
            carla_root=carla_root,
            package_url=package_url,
            package_path=package_path,
            package_size_bytes=package_size,
            disk_free_bytes=_disk_free(carla_root),
            required_free_bytes=required_free,
            desired_maps=config.desired_maps,
            candidates=candidates,
            archive_members_sample=archive_sample,
            extracted_count=extracted_count,
            map_markers=markers,
            blockers=result_blockers,
        )
    except Exception as exc:
        return CarlaMapsInstallResult(
            status="failed",
            dry_run=False,
            version=config.version,
            platform=platform,
            carla_root=carla_root,
            package_url=package_url,
            package_path=package_path,
            package_size_bytes=_local_file_size(package_path),
            disk_free_bytes=_disk_free(carla_root),
            required_free_bytes=required_free,
            desired_maps=config.desired_maps,
            candidates=candidates,
            archive_members_sample=(),
            extracted_count=0,
            map_markers=_find_map_markers(carla_root, config.desired_maps),
            blockers=(),
            error=str(exc),
        )


def default_additional_maps_url(version: str, platform: str) -> str:
    normalized = platform.lower()
    if normalized in {"windows", "win"}:
        return (
            "https://carla-releases.s3.us-east-005.backblazeb2.com/"
            f"Windows/AdditionalMaps_{version}.zip"
        )
    if normalized in {"ubuntu", "linux"}:
        return (
            "https://carla-releases.s3.us-east-005.backblazeb2.com/"
            f"Linux/AdditionalMaps_{version}.tar.gz"
        )
    raise ValueError(f"Unsupported CARLA AdditionalMaps platform: {platform}")


def probe_carla_map_inventory(
    config: CarlaMapProbeConfig,
    *,
    client_factory: Callable[[str, int], Any] | None = None,
) -> CarlaMapInventory:
    if client_factory is None:
        try:
            carla = importlib.import_module("carla")
        except ImportError as exc:
            return CarlaMapInventory(
                connected=False,
                host=config.host,
                port=config.port,
                server_version=None,
                client_version=None,
                current_map=None,
                available_maps=(),
                load_attempts=(),
                error=(
                    f"CARLA Python package is unavailable: {exc}. "
                    "Run through scripts/run_carla_client_docker.sh or install carla==0.9.16."
                ),
            )
        client_factory = carla.Client
        client_version_fallback = str(getattr(carla, "__version__", "")) or None
    else:
        client_version_fallback = None

    try:
        client = client_factory(config.host, config.port)
        if hasattr(client, "set_timeout"):
            client.set_timeout(config.timeout_s)
        world = client.get_world()
        current_map = _world_map_name(world)
        available_maps = tuple(str(item) for item in client.get_available_maps())
        attempts: list[CarlaMapLoadAttempt] = []
        if config.attempt_load:
            for map_name in config.desired_maps:
                attempts.append(_attempt_map_load(client, map_name))
        return CarlaMapInventory(
            connected=True,
            host=config.host,
            port=config.port,
            server_version=_maybe_call(client, "get_server_version"),
            client_version=_maybe_call(client, "get_client_version")
            or client_version_fallback,
            current_map=current_map,
            available_maps=available_maps,
            load_attempts=tuple(attempts),
        )
    except Exception as exc:
        return CarlaMapInventory(
            connected=False,
            host=config.host,
            port=config.port,
            server_version=None,
            client_version=client_version_fallback,
            current_map=None,
            available_maps=(),
            load_attempts=(),
            error=f"CARLA map inventory probe failed: {exc}",
        )


def write_carla_maps_report(
    run_dir: Path,
    result: CarlaMapsInstallResult | CarlaMapInventory,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_jsonable()
    if isinstance(result, CarlaMapsInstallResult):
        json_path = run_dir / "carla_maps_install.json"
        report_path = run_dir / "carla_maps_install.md"
        report = _install_markdown(result)
    else:
        json_path = run_dir / "carla_map_inventory.json"
        report_path = run_dir / "carla_map_inventory.md"
        report = _inventory_markdown(result)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(report, encoding="utf-8")
    return {**payload, "json_path": str(json_path), "report_path": str(report_path)}


def _maybe_str(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _maybe_path(value: object) -> Path | None:
    if value in (None, ""):
        return None
    return _expand_path(Path(str(value)))


def _expand_path(path: Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


def _split_csv(value: object, default: tuple[str, ...]) -> tuple[str, ...]:
    if value in (None, ""):
        return default
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    items = tuple(item.strip() for item in str(value).split(",") if item.strip())
    return items or default


def _split_paths(value: object) -> tuple[Path, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(_expand_path(Path(str(item))) for item in value if str(item).strip())
    return tuple(
        _expand_path(Path(item.strip()))
        for item in str(value).split(",")
        if item.strip()
    )


def _default_search_paths() -> list[Path]:
    paths: list[Path] = []
    env_root = os.environ.get("CARLA_ROOT")
    if env_root:
        paths.append(Path(env_root))
    paths.extend(
        [
            Path("~/Applications/Sikarugir/CARLA.app"),
            Path("/Users/kenjipcx/Applications/Sikarugir/CARLA.app"),
            Path("/Applications/CARLA.app"),
            Path("~/CARLA_0.9.16"),
            Path("/opt/carla-simulator"),
            Path("/workspace/CARLA_0.9.16"),
        ]
    )
    return paths


def _candidates_for_path(path: Path) -> list[CarlaInstallCandidate]:
    if not path.exists():
        return [
            CarlaInstallCandidate(
                path=path,
                source="search_path",
                platform="unknown",
                exists=False,
                writable=False,
                executable_path=None,
                confidence=0,
                notes=("path does not exist",),
            )
        ]
    roots: dict[Path, tuple[Path | None, str]] = {}
    if _looks_like_carla_root(path):
        roots[path] = (_find_executable(path), "search_path")
    if path.suffix == ".app" or path.is_dir():
        for executable in _find_carla_executables(path):
            root = _root_from_executable(executable)
            roots[root] = (executable, "executable_scan")

    candidates = [
        _candidate_from_root(root, executable, source)
        for root, (executable, source) in roots.items()
    ]
    return candidates or [_candidate_from_root(path, None, "search_path")]


def _looks_like_carla_root(path: Path) -> bool:
    return any(
        [
            (path / "CarlaUE4.exe").exists(),
            (path / "CarlaUE4.sh").exists(),
            (path / "PythonAPI" / "carla").exists(),
            (path / "CarlaUE4" / "Content").exists(),
            (path / "Engine").exists(),
        ]
    )


def _find_carla_executables(root: Path, max_depth: int = 12) -> list[Path]:
    names = {"CarlaUE4.exe", "CarlaUE4.sh", "CarlaUE4-Win64-Shipping.exe"}
    found: list[Path] = []
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        if len(current.parts) - root_depth >= max_depth:
            dirnames[:] = []
        for filename in filenames:
            if filename in names:
                found.append(current / filename)
    return found


def _find_executable(root: Path) -> Path | None:
    for name in ("CarlaUE4.exe", "CarlaUE4.sh"):
        path = root / name
        if path.exists():
            return path
    nested = root / "CarlaUE4" / "Binaries" / "Win64" / "CarlaUE4-Win64-Shipping.exe"
    return nested if nested.exists() else None


def _root_from_executable(executable: Path) -> Path:
    for parent in [executable.parent, *executable.parents]:
        if _looks_like_carla_root(parent):
            return parent
    if executable.name == "CarlaUE4-Win64-Shipping.exe" and len(executable.parents) >= 4:
        return executable.parents[3]
    return executable.parent


def _candidate_from_root(
    root: Path,
    executable: Path | None,
    source: str,
) -> CarlaInstallCandidate:
    notes: list[str] = []
    confidence = 0
    if _looks_like_carla_root(root):
        confidence += 50
    else:
        notes.append("no standard CARLA root markers found")
    if executable is not None and executable.exists():
        confidence += 25
    if (root / "PythonAPI" / "carla").exists():
        confidence += 10
    if (root / "Import").exists():
        confidence += 5
    platform = _platform_from_root(root, executable)
    writable = os.access(root, os.W_OK)
    if not writable:
        notes.append("root is not writable")
    return CarlaInstallCandidate(
        path=root,
        source=source,
        platform=platform,
        exists=root.exists(),
        writable=writable,
        executable_path=executable,
        confidence=confidence,
        notes=tuple(notes),
    )


def _platform_from_root(root: Path, executable: Path | None) -> str:
    executable_name = executable.name if executable is not None else ""
    if executable_name.endswith(".exe") or (root / "CarlaUE4.exe").exists():
        return "windows"
    if executable_name.endswith(".sh") or (root / "CarlaUE4.sh").exists():
        return "ubuntu"
    return "unknown"


def _resolve_carla_root(
    configured: Path | None,
    candidates: tuple[CarlaInstallCandidate, ...],
) -> Path | None:
    if configured is not None:
        return configured.expanduser().resolve()
    for candidate in candidates:
        if candidate.exists and candidate.writable and candidate.confidence >= 50:
            return candidate.path.resolve()
    for candidate in candidates:
        if candidate.exists and candidate.confidence >= 50:
            return candidate.path.resolve()
    return None


def _resolve_platform(platform: str, carla_root: Path | None) -> str:
    if platform != "auto":
        return platform
    if carla_root is None:
        return "windows" if os.name == "nt" else "ubuntu"
    if (carla_root / "CarlaUE4.exe").exists():
        return "windows"
    if (carla_root / "CarlaUE4.sh").exists():
        return "ubuntu"
    return "windows" if carla_root.suffix == ".app" else "ubuntu"


def _default_package_path(cache_dir: Path, version: str, platform: str) -> Path:
    suffix = ".zip" if platform in {"windows", "win"} else ".tar.gz"
    return cache_dir / f"AdditionalMaps_{version}{suffix}"


def _local_file_size(path: Path | None) -> int | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    return path.stat().st_size


def _remote_file_size(url: str | None) -> int | None:
    if url is None:
        return None
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            length = response.headers.get("Content-Length")
            return int(length) if length is not None else None
    except Exception:
        return None


def _disk_free(path: Path) -> int | None:
    target = path if path.exists() else path.parent
    try:
        return shutil.disk_usage(target).free
    except FileNotFoundError:
        return None


def _required_free_bytes(package_size: int | None, fallback: int) -> int:
    if package_size is None:
        return fallback
    return max(fallback, int(package_size * 2.2) + 1024 * 1024 * 1024)


def _install_preflight_blockers(
    *,
    carla_root: Path | None,
    package_path: Path,
    disk_free: int | None,
    required_free: int,
) -> list[str]:
    blockers: list[str] = []
    if carla_root is None:
        blockers.append("No CARLA install root found.")
    elif not carla_root.exists():
        blockers.append(f"CARLA root does not exist: {carla_root}")
    elif not carla_root.is_dir():
        blockers.append(f"CARLA root is not a directory: {carla_root}")
    elif not os.access(carla_root, os.W_OK):
        blockers.append(f"CARLA root is not writable: {carla_root}")
    if package_path.exists() and not package_path.is_file():
        blockers.append(f"AdditionalMaps package path is not a file: {package_path}")
    if disk_free is not None and disk_free < required_free:
        blockers.append(
            f"Insufficient free disk near CARLA root/cache: {disk_free} bytes free, "
            f"{required_free} bytes required."
        )
    return blockers


def _download_file(url: str, target: Path) -> None:
    temp_path = target.with_suffix(target.suffix + ".partial")
    resume_from = temp_path.stat().st_size if temp_path.exists() else 0
    headers = {"Range": f"bytes={resume_from}-"} if resume_from else {}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        mode = "ab" if resume_from and getattr(response, "status", 200) == 206 else "wb"
        with temp_path.open(mode) as handle:
            shutil.copyfileobj(response, handle, length=1024 * 1024)
    temp_path.replace(target)


def _archive_members_sample(package_path: Path, limit: int) -> list[str]:
    if zipfile.is_zipfile(package_path):
        with zipfile.ZipFile(package_path) as archive:
            return archive.namelist()[:limit]
    if tarfile.is_tarfile(package_path):
        with tarfile.open(package_path) as archive:
            return archive.getnames()[:limit]
    raise ValueError(f"Unsupported AdditionalMaps archive: {package_path}")


def _extract_archive(package_path: Path, target_root: Path) -> int:
    if zipfile.is_zipfile(package_path):
        with zipfile.ZipFile(package_path) as archive:
            names = archive.namelist()
            _validate_archive_paths(target_root, names)
            archive.extractall(target_root)
            return len(names)
    if tarfile.is_tarfile(package_path):
        with tarfile.open(package_path) as archive:
            members = archive.getmembers()
            _validate_archive_paths(target_root, [member.name for member in members])
            archive.extractall(target_root, members=members)
            return len(members)
    raise ValueError(f"Unsupported AdditionalMaps archive: {package_path}")


def _validate_archive_paths(target_root: Path, names: Iterable[str]) -> None:
    resolved_root = target_root.resolve()
    for name in names:
        resolved = (resolved_root / name).resolve()
        if os.path.commonpath([str(resolved_root), str(resolved)]) != str(resolved_root):
            raise ValueError(f"Unsafe archive member escapes CARLA root: {name}")


def _find_map_markers(
    carla_root: Path | None,
    desired_maps: tuple[str, ...],
    limit_per_map: int = 20,
) -> dict[str, list[str]]:
    markers = {name: [] for name in desired_maps}
    if carla_root is None or not carla_root.exists():
        return markers
    lowered = {name.lower(): name for name in desired_maps}
    for dirpath, dirnames, filenames in os.walk(carla_root):
        current = Path(dirpath)
        names = [*filenames, *dirnames]
        for entry in names:
            entry_lower = entry.lower()
            for desired_lower, desired in lowered.items():
                if desired_lower in entry_lower and len(markers[desired]) < limit_per_map:
                    markers[desired].append(str(current / entry))
        if all(len(paths) >= limit_per_map for paths in markers.values()):
            break
    return markers


def _maybe_call(obj: object, name: str) -> str | None:
    method = getattr(obj, name, None)
    if method is None:
        return None
    try:
        return str(method())
    except Exception:
        return None


def _world_map_name(world: object) -> str | None:
    try:
        world_map = world.get_map()
        return str(getattr(world_map, "name", "")) or None
    except Exception:
        return None


def _attempt_map_load(client: object, map_name: str) -> CarlaMapLoadAttempt:
    try:
        world = client.load_world(map_name)
        loaded = _world_map_name(world)
        return CarlaMapLoadAttempt(
            map_name=map_name,
            success=_map_name_matches(loaded, map_name),
            loaded_map=loaded,
        )
    except Exception as exc:
        return CarlaMapLoadAttempt(
            map_name=map_name,
            success=False,
            loaded_map=None,
            error=str(exc),
        )


def _map_name_matches(observed: str | None, desired: str) -> bool:
    if observed is None:
        return False
    normalized = observed.replace("\\", "/").rstrip("/").split("/")[-1].lower()
    return normalized == desired.lower()


def _install_markdown(result: CarlaMapsInstallResult) -> str:
    lines = [
        "# CARLA AdditionalMaps Install",
        "",
        f"- status: `{result.status}`",
        f"- dry_run: `{result.dry_run}`",
        f"- version: `{result.version}`",
        f"- platform: `{result.platform}`",
        f"- carla_root: `{result.carla_root}`",
        f"- package_url: `{result.package_url}`",
        f"- package_path: `{result.package_path}`",
        f"- package_size_bytes: `{result.package_size_bytes}`",
        f"- disk_free_bytes: `{result.disk_free_bytes}`",
        f"- required_free_bytes: `{result.required_free_bytes}`",
        f"- extracted_count: `{result.extracted_count}`",
    ]
    if result.error:
        lines.append(f"- error: `{result.error}`")
    if result.blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in result.blockers)
    lines.extend(["", "## Desired Map Markers", ""])
    for map_name, paths in result.map_markers.items():
        lines.append(f"- `{map_name}`: `{len(paths)}` marker(s)")
        lines.extend(f"  - `{path}`" for path in paths[:5])
    if result.candidates:
        lines.extend(["", "## Candidate Roots", ""])
        for candidate in result.candidates[:10]:
            lines.append(
                f"- `{candidate.path}` platform=`{candidate.platform}` "
                f"writable=`{candidate.writable}` confidence=`{candidate.confidence}`"
            )
    if result.archive_members_sample:
        lines.extend(["", "## Archive Sample", ""])
        lines.extend(f"- `{member}`" for member in result.archive_members_sample)
    lines.append("")
    return "\n".join(lines)


def _inventory_markdown(result: CarlaMapInventory) -> str:
    status = "connected" if result.connected else "failed"
    lines = [
        "# CARLA Map Inventory",
        "",
        f"- status: `{status}`",
        f"- endpoint: `{result.host}:{result.port}`",
        f"- current_map: `{result.current_map}`",
        f"- server_version: `{result.server_version}`",
        f"- client_version: `{result.client_version}`",
        f"- available_map_count: `{len(result.available_maps)}`",
    ]
    if result.error:
        lines.append(f"- error: `{result.error}`")
    if result.load_attempts:
        lines.extend(["", "## Load Attempts", ""])
        for attempt in result.load_attempts:
            lines.append(
                f"- `{attempt.map_name}` success=`{attempt.success}` "
                f"loaded_map=`{attempt.loaded_map}` error=`{attempt.error}`"
            )
    if result.available_maps:
        lines.extend(["", "## Available Maps", ""])
        lines.extend(f"- `{map_name}`" for map_name in result.available_maps)
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "CarlaInstallCandidate",
    "CarlaMapInventory",
    "CarlaMapLoadAttempt",
    "CarlaMapProbeConfig",
    "CarlaMapsInstallConfig",
    "CarlaMapsInstallResult",
    "default_additional_maps_url",
    "discover_carla_install_candidates",
    "install_carla_additional_maps",
    "load_carla_map_probe_config",
    "load_carla_maps_install_config",
    "probe_carla_map_inventory",
    "write_carla_maps_report",
]
