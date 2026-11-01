"""Copy travelpanda/* images from one Cloudinary cloud to another, then rewrite DB urls.

Reads OLD_* / NEW_* from env (or falls back to CLOUDINARY_* + CLOUDINARY_*_OLD).
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from urllib.parse import unquote

import cloudinary
from cloudinary.api import resources
from cloudinary.uploader import upload as cloudinary_upload
from sqlalchemy import text

from app.db.database import AsyncSessionLocal

PREFIX = "travelpanda"
PUBLIC_ID_RE = re.compile(
    r"/image/upload/(?:[^/]+/)*v\d+/(.+)\.(?:jpe?g|png|webp|gif|avif|bmp|tiff?)$",
    re.IGNORECASE,
)


def _creds(prefix: str, fallback_prefix: str | None = None) -> dict:
    cloud = os.getenv(f"{prefix}_CLOUD_NAME") or (
        os.getenv(f"{fallback_prefix}_CLOUD_NAME") if fallback_prefix else None
    )
    key = os.getenv(f"{prefix}_API_KEY") or (
        os.getenv(f"{fallback_prefix}_API_KEY") if fallback_prefix else None
    )
    secret = os.getenv(f"{prefix}_API_SECRET") or (
        os.getenv(f"{fallback_prefix}_API_SECRET") if fallback_prefix else None
    )
    if not (cloud and key and secret):
        raise SystemExit(f"missing credentials for {prefix} (and fallback {fallback_prefix})")
    return {"cloud_name": cloud.strip(), "api_key": key.strip(), "api_secret": secret.strip()}


def configure(creds: dict) -> None:
    cloudinary.config(**creds, secure=True)


def list_images(old: dict, prefix: str) -> list[dict]:
    configure(old)
    items: list[dict] = []
    next_cursor = None
    while True:
        kwargs: dict = {
            "type": "upload",
            "resource_type": "image",
            "prefix": prefix,
            "max_results": 500,
        }
        if next_cursor:
            kwargs["next_cursor"] = next_cursor
        res = resources(**kwargs)
        items.extend(res.get("resources", []))
        next_cursor = res.get("next_cursor")
        if not next_cursor:
            break
    return items


def copy_images(new: dict, items: list[dict]) -> dict[str, str]:
    configure(new)
    mapping: dict[str, str] = {}
    failed: list[tuple[str, str]] = []

    for i, item in enumerate(items, start=1):
        public_id = item["public_id"]
        source_url = item.get("secure_url") or item.get("url")
        if not source_url:
            failed.append((public_id, "missing source url"))
            continue
        try:
            result = cloudinary_upload(
                source_url,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
            )
            new_url = result.get("secure_url")
            if not new_url:
                failed.append((public_id, "upload returned no url"))
                continue
            mapping[public_id] = new_url
            print(f"[{i}/{len(items)}] ok  {public_id}")
        except Exception as exc:  # noqa: BLE001
            failed.append((public_id, str(exc)))
            print(f"[{i}/{len(items)}] FAIL {public_id}: {exc}", file=sys.stderr)

    if failed:
        print(f"\n{len(failed)} failures:", file=sys.stderr)
        for pid, err in failed:
            print(f"  - {pid}: {err}", file=sys.stderr)
    return mapping


def extract_public_id(url: str) -> str | None:
    match = PUBLIC_ID_RE.search(unquote(url))
    return match.group(1) if match else None


def rewrite_url(url: str | None, old_cloud: str, new_cloud: str, mapping: dict[str, str]) -> str | None:
    if not url or old_cloud not in url:
        return url
    public_id = extract_public_id(url)
    if public_id and public_id in mapping:
        return mapping[public_id]
    return url.replace(
        f"res.cloudinary.com/{old_cloud}/",
        f"res.cloudinary.com/{new_cloud}/",
    )


async def rewrite_db_urls(old_cloud: str, new_cloud: str, mapping: dict[str, str]) -> None:
    tables_cols = [
        ("destinations", "cover_image_url"),
        ("hotels", "cover_image_url"),
        ("packages", "cover_image_url"),
        ("package_media", "url"),
    ]
    async with AsyncSessionLocal() as db:
        updated = 0
        for table, col in tables_cols:
            rows = (
                await db.execute(
                    text(
                        f"SELECT id, {col} AS url FROM {table} "
                        f"WHERE {col} IS NOT NULL AND {col} LIKE :pat"
                    ),
                    {"pat": f"%res.cloudinary.com/{old_cloud}/%"},
                )
            ).mappings().all()
            for row in rows:
                new_url = rewrite_url(row["url"], old_cloud, new_cloud, mapping)
                if new_url == row["url"]:
                    continue
                await db.execute(
                    text(f"UPDATE {table} SET {col} = :url WHERE id = :id"),
                    {"url": new_url, "id": row["id"]},
                )
                updated += 1
                print(f"db {table}.{col} id={row['id']}")
        await db.commit()
        print(f"db rows updated: {updated}")


def main() -> None:
    # after .env swap: NEW = CLOUDINARY_*, OLD = CLOUDINARY_*_OLD
    new = _creds("CLOUDINARY")
    old = _creds("CLOUDINARY_OLD")

    print(f"listing {PREFIX}/* from {old['cloud_name']} ...")
    items = list_images(old, PREFIX)
    print(f"found {len(items)} images")
    if not items:
        raise SystemExit("nothing to migrate")

    print(f"uploading to {new['cloud_name']} ...")
    mapping = copy_images(new, items)
    print(f"copied {len(mapping)}/{len(items)}")

    print("rewriting db urls ...")
    asyncio.run(rewrite_db_urls(old["cloud_name"], new["cloud_name"], mapping))
    print("done")


if __name__ == "__main__":
    main()
