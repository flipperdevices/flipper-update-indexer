import hashlib
import tempfile

import boto3
from moto import mock_aws

from src.storage import LocalStorage, S3Storage

SHA_HELLO = hashlib.sha256(b"hello").hexdigest()


def test_local_storage_roundtrip():
    storage = LocalStorage(root=tempfile.mkdtemp())
    storage.write(b"hello", "busybar-firmware", "0.9.2", "busybar-f22-0.9.2.tgz")
    storage.write(b"tok", "busybar-firmware", "0.9.2", ".version_id")
    assert sorted(storage.list_files("busybar-firmware", "0.9.2")) == [
        ".version_id",
        "busybar-f22-0.9.2.tgz",
    ]
    assert storage.list_dirs("busybar-firmware") == ["0.9.2"]
    assert (
        storage.sha256("busybar-firmware", "0.9.2", "busybar-f22-0.9.2.tgz")
        == SHA_HELLO
    )
    kind, _ = storage.serving_target("busybar-firmware/0.9.2/busybar-f22-0.9.2.tgz")
    assert kind == "file"


def test_local_storage_blocks_path_traversal():
    storage = LocalStorage(root=tempfile.mkdtemp())
    assert storage.serving_target("../../etc/passwd") is None


def test_local_storage_walk_and_delete():
    storage = LocalStorage(root=tempfile.mkdtemp())
    storage.write(b"a", "busybar-firmware", "dev", "f.tgz")
    storage.write(b"b", "busybar-firmware", "0.9.2", "g.tgz")
    walked = {d: sorted(f) for d, f in storage.walk("busybar-firmware")}
    assert walked == {"dev": ["f.tgz"], "0.9.2": ["g.tgz"]}
    storage.delete_tree("busybar-firmware", "dev")
    assert storage.list_dirs("busybar-firmware") == ["0.9.2"]


@mock_aws
def test_s3_storage_roundtrip():
    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="firmware-bucket")
    storage = S3Storage(
        bucket="firmware-bucket",
        prefix="builds",
        region="us-east-1",
        access_key="testing",
        secret_key="testing",
    )
    storage.write(b"hello", "busybar-firmware", "0.9.2", "busybar-f22-0.9.2.tgz")
    storage.write(b"tok", "busybar-firmware", "0.9.2", ".version_id")
    assert sorted(storage.list_files("busybar-firmware", "0.9.2")) == [
        ".version_id",
        "busybar-f22-0.9.2.tgz",
    ]
    assert storage.list_dirs("busybar-firmware") == ["0.9.2"]
    # sha256 is read from object metadata written at upload (no re-download)
    assert (
        storage.sha256("busybar-firmware", "0.9.2", "busybar-f22-0.9.2.tgz")
        == SHA_HELLO
    )
    kind, url = storage.serving_target("busybar-firmware/0.9.2/busybar-f22-0.9.2.tgz")
    assert kind == "redirect"
    assert "firmware-bucket" in url


@mock_aws
def test_s3_storage_walk_and_delete():
    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="walk-bucket")
    storage = S3Storage(
        bucket="walk-bucket",
        prefix="builds",
        region="us-east-1",
        access_key="x",
        secret_key="y",
    )
    storage.write(b"a", "busybar-firmware", "dev", "f.tgz")
    storage.write(b"b", "busybar-firmware", "0.9.2", "g.tgz")
    walked = {d: sorted(f) for d, f in storage.walk("busybar-firmware")}
    assert walked == {"dev": ["f.tgz"], "0.9.2": ["g.tgz"]}
    storage.delete_tree("busybar-firmware", "dev")
    assert storage.list_dirs("busybar-firmware") == ["0.9.2"]
    assert storage.list_files("busybar-firmware", "dev") == []
