from urllib.parse import urlparse
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from app.services.storage.base import ProviderMetadata, StorageProvider


def _normalize_s3_endpoint(raw_endpoint: str, bucket: str) -> str:
    """Normalize custom S3 endpoint URL (strips accidental trailing /<bucket> from Sabay bucket URLs)."""
    cleaned = raw_endpoint.strip().rstrip("/")
    if not cleaned:
        return ""

    # If user pasted full Sabay bucket URL like https://fsgw.sabay.com/bucket03, strip /bucket03
    if bucket:
        suffix = f"/{bucket}"
        if cleaned.lower().endswith(suffix.lower()):
            cleaned = cleaned[: -len(suffix)].rstrip("/")

    return cleaned


class S3CompatibleStorageProvider(StorageProvider):
    """Generic S3-compatible provider supporting Sabay Cloud, AWS S3, Cloudflare R2, and MinIO."""

    metadata = ProviderMetadata(
        id="s3_compatible",
        label="S3-Compatible Object Storage",
        description="Connect Sabay Cloud Storage, AWS S3, Cloudflare R2, DigitalOcean Spaces, or MinIO.",
        supports_cdn=True,
    )

    def __init__(
        self,
        endpoint_url: str = "",
        region: str = "us-east-1",
        bucket: str = "",
        access_key_id: str = "",
        secret_access_key: str = "",
        public_base_url: str = "",
        folder: str = "waste_reports",
    ) -> None:
        self.bucket = bucket.strip().strip("/")
        self.raw_endpoint_url = endpoint_url.strip().rstrip("/")
        self.endpoint_url = _normalize_s3_endpoint(endpoint_url, self.bucket)
        self.region = region.strip() or "us-east-1"
        self.access_key_id = access_key_id.strip()
        self.secret_access_key = secret_access_key.strip()
        self.public_base_url = public_base_url.strip().rstrip("/")
        self.folder = folder.strip().strip("/") or "waste_reports"

    @property
    def is_configured(self) -> bool:
        return bool(self.bucket and self.access_key_id and self.secret_access_key)

    def _validate_endpoint(self) -> str | None:
        if not self.endpoint_url:
            return None
        parsed = urlparse(self.endpoint_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return f"Invalid Endpoint URL '{self.endpoint_url}'. Must start with https:// or http://."
        if "graphql" in parsed.path.lower() or "cloudgateway.sabay.com" in parsed.netloc.lower():
            return (
                "Endpoint URL points to Sabay's GraphQL management gateway (cloudgateway.sabay.com/graphql). "
                "For S3 uploads, enter only the S3 storage gateway origin from your bucket's `url` field "
                "(for example: https://fsgw.sabay.com — without /bucketName or /graphql)."
            )
        return None

    def _build_client(self):
        if not self.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "S3-compatible storage is not configured. Configure bucket, access key, and secret "
                    "in Admin Console -> Settings -> File Storage."
                ),
            )
        endpoint_error = self._validate_endpoint()
        if endpoint_error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=endpoint_error)

        kwargs: dict = {
            "region_name": self.region,
            "aws_access_key_id": self.access_key_id,
            "aws_secret_access_key": self.secret_access_key,
        }
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
            # Custom S3 gateways (Sabay Cloud fsgw, MinIO, Ceph RGW) use path-style URLs + SigV4
            kwargs["config"] = BotoConfig(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )
        return boto3.client("s3", **kwargs)

    def _object_key(self, public_id: str, extension: str) -> str:
        filename = f"{public_id}.{extension}"
        return f"{self.folder}/{filename}" if self.folder else filename

    def upload(self, contents: bytes, public_id: str, extension: str, content_type: str) -> str:
        client = self._build_client()
        object_key = self._object_key(public_id, extension)
        try:
            # Set ACL='public-read' so Sabay Cloud, Ceph, MinIO, and S3 make uploaded photos publicly viewable
            try:
                client.put_object(
                    Bucket=self.bucket,
                    Key=object_key,
                    Body=contents,
                    ContentType=content_type,
                    ACL="public-read",
                )
            except ClientError as acl_err:
                err_code = str(acl_err.response.get("Error", {}).get("Code", ""))
                # If bucket has ACLs disabled (e.g. AWS S3 BucketOwnerEnforced), fall back to put_object without ACL
                if "AccessControlListNotSupported" in err_code or "InvalidRequest" in err_code or "InvalidArgument" in err_code:
                    client.put_object(
                        Bucket=self.bucket,
                        Key=object_key,
                        Body=contents,
                        ContentType=content_type,
                    )
                else:
                    raise
        except (ClientError, BotoCoreError, Exception) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to upload image to S3-compatible storage: {exc}",
            ) from exc

        if self.public_base_url:
            return f"{self.public_base_url}/{object_key}"
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket}/{object_key}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{object_key}"

    def delete(self, public_id: str, extension: str) -> None:
        self._build_client().delete_object(Bucket=self.bucket, Key=self._object_key(public_id, extension))

    def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Missing S3-compatible storage credentials (bucket, access key ID, secret access key)."

        endpoint_error = self._validate_endpoint()
        if endpoint_error:
            return False, endpoint_error

        try:
            client = self._build_client()
            client.head_bucket(Bucket=self.bucket)
            target = f"{self.endpoint_url}/{self.bucket}" if self.endpoint_url else self.bucket
            return True, f"Connected to bucket '{self.bucket}' ({target}) successfully."
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status_code == 404 or code in {"404", "NoSuchBucket", "NotFound"}:
                # Check whether credentials authenticate against the gateway and list real buckets
                available = self._try_list_buckets(client)
                if available is not None:
                    if available:
                        listed = ", ".join(available)
                        return (
                            False,
                            f"Credentials are valid, but bucket '{self.bucket}' was not found on "
                            f"'{self.endpoint_url or 'S3'}'. Available buckets: {listed}",
                        )
                    return (
                        False,
                        f"Credentials are valid on '{self.endpoint_url or 'S3'}', but no buckets exist yet. "
                        f"Create bucket '{self.bucket}' first (e.g. via Sabay Cloud dashboard or s3_createBucket).",
                    )
                return (
                    False,
                    f"404 Not Found for '{self.endpoint_url or 'S3'}/{self.bucket}'. "
                    "Verify that Endpoint URL is the base S3 gateway host (e.g. https://fsgw.sabay.com, "
                    "not the GraphQL URL and without a trailing bucket path) and that the bucket exists.",
                )
            return False, f"S3-compatible connection failed ({code or status_code}): {exc}"
        except Exception as exc:
            return False, f"S3-compatible connection failed: {exc}"

    @staticmethod
    def _try_list_buckets(client) -> list[str] | None:
        try:
            resp = client.list_buckets()
            return [b["Name"] for b in resp.get("Buckets", []) if "Name" in b]
        except Exception:
            return None
