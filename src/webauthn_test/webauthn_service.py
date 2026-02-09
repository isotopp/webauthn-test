"""WebAuthn option generation and verification adapter layer.

This module isolates direct interaction with the `webauthn` library so routes
can focus on HTTP/session concerns while this layer handles credential data
shape conversion (bytes/base64url) and descriptor construction.

Constraints:
- server challenge and credential-id conversions must remain lossless
- verification APIs are treated as the source of cryptographic truth
- transport hints are best-effort and must not break ceremony correctness
"""

from __future__ import annotations

import json
from typing import Any
from typing import cast

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, options_to_json
from webauthn.helpers.structs import (
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
)

from webauthn_test.models import Authenticator, User


def _safe_transports(raw: list[str]) -> list[AuthenticatorTransport]:
    transports: list[AuthenticatorTransport] = []
    for value in raw:
        try:
            transports.append(AuthenticatorTransport(value))
        except ValueError:
            continue
    return transports


def _descriptor_from_authenticator(
    authenticator: Authenticator,
) -> PublicKeyCredentialDescriptor:
    return PublicKeyCredentialDescriptor(
        id=cast(bytes, authenticator.credential_id),
        transports=_safe_transports(authenticator.transports_list()) or None,
    )


def begin_registration(
    *,
    user: User,
    rp_id: str,
    rp_name: str,
    exclude_authenticators: list[Authenticator],
) -> tuple[dict[str, Any], str]:
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=rp_name,
        user_name=user.username,
        user_display_name=user.full_name or user.username,
        user_id=str(user.id).encode("utf-8"),
        exclude_credentials=[
            _descriptor_from_authenticator(item) for item in exclude_authenticators
        ]
        or None,
    )
    payload = json.loads(options_to_json(options))
    challenge = str(payload["challenge"])
    return payload, challenge


def finish_registration(
    *,
    credential: dict[str, Any],
    expected_challenge: str,
    rp_id: str,
    origin: str,
):
    return verify_registration_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_rp_id=rp_id,
        expected_origin=origin,
    )


def begin_authentication(
    *,
    rp_id: str,
    allow_authenticators: list[Authenticator],
) -> tuple[dict[str, Any], str]:
    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=[
            _descriptor_from_authenticator(item) for item in allow_authenticators
        ]
        or None,
    )
    payload = json.loads(options_to_json(options))
    challenge = str(payload["challenge"])
    return payload, challenge


def finish_authentication(
    *,
    credential: dict[str, Any],
    expected_challenge: str,
    rp_id: str,
    origin: str,
    credential_public_key: bytes,
    credential_current_sign_count: int,
):
    return verify_authentication_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_rp_id=rp_id,
        expected_origin=origin,
        credential_public_key=credential_public_key,
        credential_current_sign_count=credential_current_sign_count,
    )


def credential_id_bytes_from_payload(credential: dict[str, Any]) -> bytes:
    value = credential.get("id")
    if not isinstance(value, str) or not value:
        msg = "Missing credential id."
        raise ValueError(msg)
    return base64url_to_bytes(value)


def public_key_bytes_to_b64(value: bytes) -> str:
    return bytes_to_base64url(value)
