#!/usr/bin/env python3
"""Lightweight Phase 7B POSNext PWA/offline regression verification."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE_URL = "https://pos.yemenfrappe.com"
BENCH_ROOT = Path("/home/frappe/frappe-bench")
APP_ROOT = BENCH_ROOT / "apps" / "pos_next"
SITE_FILES = BENCH_ROOT / "sites" / "pos.yemenfrappe.com" / "private" / "files"


def fetch(url: str, method: str = "GET") -> dict:
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = b"" if method == "HEAD" else response.read()
            return {
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "url": response.geturl(),
                "headers": {k.lower(): v for k, v in response.headers.items()},
                "body": body.decode("utf-8", errors="replace"),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = b"" if method == "HEAD" else exc.read()
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "headers": {k.lower(): v for k, v in exc.headers.items()},
            "body": body.decode("utf-8", errors="replace"),
            "error": str(exc),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostics script
        return {
            "ok": False,
            "status": None,
            "url": url,
            "headers": {},
            "body": "",
            "error": repr(exc),
        }


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def main() -> int:
    urls = {
        "pos": f"{BASE_URL}/pos",
        "asset_sw": f"{BASE_URL}/assets/pos_next/pos/sw.js",
        "asset_manifest": f"{BASE_URL}/assets/pos_next/pos/manifest.webmanifest",
        "pos_sw": f"{BASE_URL}/pos/sw.js",
    }

    checks = {
        key: {
            "head": fetch(url, "HEAD"),
            "get": fetch(url, "GET") if key in {"asset_manifest", "asset_sw", "pos_sw"} else None,
        }
        for key, url in urls.items()
    }

    manifest = {}
    manifest_error = None
    try:
        manifest = json.loads(checks["asset_manifest"]["get"]["body"])
    except Exception as exc:  # noqa: BLE001 - diagnostics script
        manifest_error = repr(exc)

    sw_body = checks["asset_sw"]["get"]["body"] or ""
    pos_sw_body = checks["pos_sw"]["get"]["body"] or ""
    offline_db = read_text(APP_ROOT / "POS" / "src" / "utils" / "offline" / "db.js")
    offline_sync = read_text(APP_ROOT / "POS" / "src" / "utils" / "offline" / "sync.js")
    offline_doctype = read_text(
        APP_ROOT
        / "pos_next"
        / "pos_next"
        / "doctype"
        / "offline_invoice_sync"
        / "offline_invoice_sync.json"
    )

    sw_headers = checks["asset_sw"]["head"]["headers"]
    manifest_headers = checks["asset_manifest"]["head"]["headers"]
    pos_sw_headers = checks["pos_sw"]["head"]["headers"]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "urls": urls,
        "http": {
            name: {
                "status": data["head"]["status"],
                "content_type": data["head"]["headers"].get("content-type"),
                "cache_control": data["head"]["headers"].get("cache-control"),
                "service_worker_allowed": data["head"]["headers"].get(
                    "service-worker-allowed"
                ),
                "error": data["head"]["error"],
            }
            for name, data in checks.items()
        },
        "manifest": {
            "parse_ok": manifest_error is None,
            "error": manifest_error,
            "id": manifest.get("id"),
            "start_url": manifest.get("start_url"),
            "scope": manifest.get("scope"),
            "lang": manifest.get("lang"),
            "dir": manifest.get("dir"),
            "display": manifest.get("display"),
            "icons_count": len(manifest.get("icons") or []),
            "content_type": manifest_headers.get("content-type"),
            "cache_control": manifest_headers.get("cache-control"),
            "valid_phase7a_values": {
                "id_is_pos": manifest.get("id") == "/pos",
                "start_url_is_pos": manifest.get("start_url") == "/pos",
                "scope_is_pos": manifest.get("scope") == "/pos",
                "lang_is_ar": manifest.get("lang") == "ar",
                "dir_is_rtl": manifest.get("dir") == "rtl",
            },
        },
        "service_worker": {
            "asset_url": urls["asset_sw"],
            "asset_status": checks["asset_sw"]["head"]["status"],
            "asset_content_type": sw_headers.get("content-type"),
            "asset_cache_control": sw_headers.get("cache-control"),
            "service_worker_allowed": sw_headers.get("service-worker-allowed"),
            "has_precache": "precacheAndRoute" in sw_body or "__WB_MANIFEST" in sw_body,
            "has_runtime_cache": "registerRoute" in sw_body,
            "has_clients_claim": "clientsClaim" in sw_body or "clients.claim" in sw_body,
            "pos_sw_url_returns_javascript": "javascript" in (pos_sw_headers.get("content-type") or ""),
            "pos_sw_url_looks_like_html": bool(re.search(r"<html|<!doctype html", pos_sw_body, re.I)),
            "effective_scope_risk": (
                "The SW is served from /assets/pos_next/pos/sw.js without "
                "Service-Worker-Allowed. Browser maximum scope is expected to stay "
                "under /assets/pos_next/pos/, not /pos/."
            ),
        },
        "offline_regression": {
            "dexie_db_declared": "new Dexie(\"pos_next_offline\")" in offline_db,
            "invoice_queue_declared": "invoice_queue" in offline_db,
            "invoice_queue_offline_id_unique": "&offline_id" in offline_db,
            "offline_sync_uses_offline_id": "offline_id" in offline_sync,
            "doctype_offline_id_required": '"reqd": 1' in offline_doctype
            and '"fieldname": "offline_id"' in offline_doctype,
            "doctype_offline_id_unique": '"unique": 1' in offline_doctype
            and '"fieldname": "offline_id"' in offline_doctype,
        },
    }

    result["summary"] = {
        "pos_returns_200": checks["pos"]["head"]["status"] == 200,
        "manifest_reachable": checks["asset_manifest"]["head"]["status"] == 200,
        "manifest_valid": manifest_error is None,
        "sw_reachable": checks["asset_sw"]["head"]["status"] == 200,
        "sw_headers_ready_for_pos_scope": sw_headers.get("service-worker-allowed") in {
            "/pos",
            "/pos/",
            "/",
        },
        "sw_cache_control_safe": bool(
            re.search(r"no-cache|no-store|max-age=0", sw_headers.get("cache-control") or "", re.I)
        ),
        "pos_sw_route_is_real_sw": "javascript" in (pos_sw_headers.get("content-type") or "")
        and not result["service_worker"]["pos_sw_url_looks_like_html"],
        "offline_id_protection_present": result["offline_regression"][
            "invoice_queue_offline_id_unique"
        ]
        and result["offline_regression"]["doctype_offline_id_unique"],
    }

    SITE_FILES.mkdir(parents=True, exist_ok=True)
    output_path = SITE_FILES / "posnext_phase7b_verification_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # This script is diagnostic: return 0 if core app is reachable even when headers need deployment.
    return 0 if result["summary"]["pos_returns_200"] and result["summary"]["sw_reachable"] else 1


if __name__ == "__main__":
    sys.exit(main())
