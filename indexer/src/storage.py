import os
import shutil
import hashlib
import logging
import posixpath
from typing import List, Optional, Tuple

from .settings import settings


def _hexdigest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Storage:
    """
    Storage abstraction for artifacts. Paths are passed as logical segments
    relative to the storage root (e.g. "busybar-firmware", "0.9.2", file name).
    Two backends implement it: LocalStorage (filesystem) and S3Storage (S3-compatible).
    """

    backend: str

    def ensure_root(self) -> None:
        raise NotImplementedError

    def ensure_dir(self, *parts: str) -> None:
        raise NotImplementedError

    def write(self, data: bytes, *parts: str) -> None:
        raise NotImplementedError

    def read(self, *parts: str) -> bytes:
        raise NotImplementedError

    def file_exists(self, *parts: str) -> bool:
        raise NotImplementedError

    def list_files(self, *parts: str) -> List[str]:
        raise NotImplementedError

    def list_dirs(self, *parts: str) -> List[str]:
        raise NotImplementedError

    def walk(self, *parts: str) -> List[Tuple[str, List[str]]]:
        """Return (relative_dir, file_names) for every sub-directory that holds files."""
        raise NotImplementedError

    def delete_tree(self, *parts: str) -> None:
        raise NotImplementedError

    def sha256(self, *parts: str) -> str:
        raise NotImplementedError

    def public_url(self, *parts: str) -> str:
        # Stable URL baked into directory.json; resolved by the /builds route at access time.
        suffix = "/".join(part.strip("/") for part in parts if part)
        return settings.base_url.rstrip("/") + "/" + suffix

    def serving_target(self, path: str) -> Optional[Tuple[str, str]]:
        """Resolve a /builds/<path> request to ("file", abspath) or ("redirect", url)."""
        raise NotImplementedError


class LocalStorage(Storage):
    backend = "local"

    def __init__(self, root: Optional[str] = None) -> None:
        self.root = root if root is not None else settings.files_dir

    def _abs(self, *parts: str) -> str:
        return os.path.join(self.root, *[part.strip("/") for part in parts if part])

    def ensure_root(self) -> None:
        os.makedirs(self.root, exist_ok=True)

    def ensure_dir(self, *parts: str) -> None:
        os.makedirs(self._abs(*parts), exist_ok=True)

    def write(self, data: bytes, *parts: str) -> None:
        target = self._abs(*parts)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as out_file:
            out_file.write(data)

    def read(self, *parts: str) -> bytes:
        with open(self._abs(*parts), "rb") as in_file:
            return in_file.read()

    def file_exists(self, *parts: str) -> bool:
        return os.path.isfile(self._abs(*parts))

    def list_files(self, *parts: str) -> List[str]:
        directory = self._abs(*parts)
        if not os.path.isdir(directory):
            return []
        return [
            name
            for name in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, name))
        ]

    def list_dirs(self, *parts: str) -> List[str]:
        directory = self._abs(*parts)
        if not os.path.isdir(directory):
            return []
        return [
            name
            for name in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, name))
        ]

    def walk(self, *parts: str) -> List[Tuple[str, List[str]]]:
        base = self._abs(*parts)
        if not os.path.isdir(base):
            return []
        result: List[Tuple[str, List[str]]] = []
        for root, _dirs, files in os.walk(base):
            if not files:
                continue
            relative = os.path.relpath(root, base).replace(os.sep, "/")
            result.append((relative, files))
        return result

    def delete_tree(self, *parts: str) -> None:
        target = self._abs(*parts)
        if os.path.isdir(target):
            shutil.rmtree(target)
        elif os.path.isfile(target):
            os.remove(target)

    def sha256(self, *parts: str) -> str:
        return _hexdigest(self.read(*parts))

    def serving_target(self, path: str) -> Optional[Tuple[str, str]]:
        root = os.path.abspath(self.root)
        target = os.path.abspath(os.path.join(root, path))
        # guard against path traversal escaping the storage root
        if target != root and not target.startswith(root + os.sep):
            return None
        if not os.path.isfile(target):
            return None
        return ("file", target)


class S3Storage(Storage):
    backend = "s3"

    # presigned download links are short-lived; directory.json stores stable URLs instead
    PRESIGN_TTL_SECONDS = 3600

    def __init__(
        self,
        bucket: Optional[str] = None,
        prefix: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ) -> None:
        import boto3

        self.bucket = bucket if bucket is not None else settings.s3_bucket
        if not self.bucket:
            raise ValueError("INDEXER_S3_BUCKET is required for the s3 storage backend")
        self.prefix = (prefix if prefix is not None else settings.s3_prefix).strip("/")
        self.client = boto3.session.Session().client(
            "s3",
            endpoint_url=(
                endpoint_url if endpoint_url is not None else settings.s3_endpoint_url
            ),
            region_name=region if region is not None else settings.s3_region,
            aws_access_key_id=(
                access_key if access_key is not None else settings.s3_access_key_id
            ),
            aws_secret_access_key=(
                secret_key if secret_key is not None else settings.s3_secret_access_key
            ),
        )

    def _key(self, *parts: str) -> str:
        segments = [self.prefix] + [part.strip("/") for part in parts if part]
        return "/".join(segment for segment in segments if segment)

    def _dir_prefix(self, *parts: str) -> str:
        key = self._key(*parts)
        return key + "/" if key else ""

    def ensure_root(self) -> None:
        return None

    def ensure_dir(self, *parts: str) -> None:
        return None

    def write(self, data: bytes, *parts: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key(*parts),
            Body=data,
            Metadata={"sha256": _hexdigest(data)},
        )

    def read(self, *parts: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=self._key(*parts))
        return response["Body"].read()

    def file_exists(self, *parts: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(*parts))
            return True
        except ClientError:
            return False

    def list_files(self, *parts: str) -> List[str]:
        prefix = self._dir_prefix(*parts)
        names: List[str] = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=self.bucket, Prefix=prefix, Delimiter="/"
        ):
            for item in page.get("Contents", []):
                name = item["Key"][len(prefix) :]
                if name:
                    names.append(name)
        return names

    def list_dirs(self, *parts: str) -> List[str]:
        prefix = self._dir_prefix(*parts)
        names: List[str] = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=self.bucket, Prefix=prefix, Delimiter="/"
        ):
            for item in page.get("CommonPrefixes", []):
                names.append(item["Prefix"][len(prefix) :].rstrip("/"))
        return names

    def walk(self, *parts: str) -> List[Tuple[str, List[str]]]:
        prefix = self._dir_prefix(*parts)
        grouped: dict = {}
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for item in page.get("Contents", []):
                relative = item["Key"][len(prefix) :]
                if not relative:
                    continue
                relative_dir = posixpath.dirname(relative) or "."
                grouped.setdefault(relative_dir, []).append(
                    posixpath.basename(relative)
                )
        return list(grouped.items())

    def delete_tree(self, *parts: str) -> None:
        prefix = self._dir_prefix(*parts)
        paginator = self.client.get_paginator("list_objects_v2")
        batch: List[dict] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for item in page.get("Contents", []):
                batch.append({"Key": item["Key"]})
                if len(batch) == 1000:
                    self.client.delete_objects(
                        Bucket=self.bucket, Delete={"Objects": batch}
                    )
                    batch = []
        if batch:
            self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": batch})

    def sha256(self, *parts: str) -> str:
        response = self.client.head_object(Bucket=self.bucket, Key=self._key(*parts))
        stored = response.get("Metadata", {}).get("sha256")
        if stored:
            return stored
        # objects uploaded out-of-band may lack the metadata: fall back to hashing
        return _hexdigest(self.read(*parts))

    def serving_target(self, path: str) -> Optional[Tuple[str, str]]:
        key = self._key(path)
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self.PRESIGN_TTL_SECONDS,
        )
        return ("redirect", url)


def build_storage() -> Storage:
    if settings.storage_backend == "s3":
        return S3Storage()
    if settings.storage_backend == "local":
        return LocalStorage()
    raise ValueError(f"Unknown INDEXER_STORAGE_BACKEND: {settings.storage_backend}")


storage = build_storage()
