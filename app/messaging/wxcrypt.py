"""WXBizMsgCrypt — shared AES message crypto for WeChat OA & WeCom callbacks.

Implements Tencent's official encrypt/decrypt scheme so EIOS can receive
encrypted (安全模式 / 密文模式) callbacks and therefore actually reply on
WeChat Official Account and WeCom:

  * AES-256-CBC with PKCS#7 padding, key = base64(EncodingAESKey + "=")
  * IV = first 16 bytes of the AES key
  * plaintext layout: random(16) | msg_len(4, big-endian) | msg | receive_id
  * message signature = sha1(sorted(token, timestamp, nonce, encrypt))

This is pure crypto with no network, so it is fully unit-testable offline via
an encrypt -> decrypt round trip (see tests/test_wxcrypt.py).
"""

from __future__ import annotations

import base64
import hashlib
import os
import struct
import time
from xml.etree import ElementTree

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class WXCryptError(Exception):
    """Raised on signature mismatch, bad padding, or malformed payloads."""


def _pkcs7_pad(data: bytes, block: int = 32) -> bytes:
    pad = block - (len(data) % block)
    return data + bytes([pad]) * pad


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        raise WXCryptError("empty plaintext")
    pad = data[-1]
    if pad < 1 or pad > 32 or pad > len(data):
        raise WXCryptError("bad PKCS7 padding")
    return data[:-pad]


def message_signature(token: str, timestamp: str, nonce: str, encrypt: str) -> str:
    """SHA1 of the sorted (token, timestamp, nonce, encrypt) tuple (spec-mandated)."""
    raw = "".join(sorted([token, timestamp, nonce, encrypt]))
    return hashlib.sha1(raw.encode()).hexdigest()  # noqa: S324 (WeChat spec mandates sha1)


def extract_encrypt(xml_body: str) -> str:
    """Pull the <Encrypt> CDATA out of an encrypted callback body."""
    try:
        root = ElementTree.fromstring(xml_body)
    except Exception as exc:  # noqa: BLE001
        raise WXCryptError("invalid callback XML") from exc
    node = root.find("Encrypt")
    if node is None or not (node.text or "").strip():
        raise WXCryptError("no <Encrypt> in callback body")
    return node.text.strip()


class WXBizMsgCrypt:
    """Encrypt/decrypt helper for one channel (fixed token, AES key, receive_id).

    receive_id is the CorpID for WeCom and the AppID for a WeChat OA.
    """

    def __init__(self, token: str, encoding_aes_key: str, receive_id: str) -> None:
        if len(encoding_aes_key) != 43:
            raise WXCryptError("EncodingAESKey must be 43 characters")
        self.token = token
        self.key = base64.b64decode(encoding_aes_key + "=")
        if len(self.key) != 32:
            raise WXCryptError("AES key must decode to 32 bytes")
        self.iv = self.key[:16]
        self.receive_id = receive_id

    def _aes_encrypt(self, plain: bytes) -> bytes:
        enc = Cipher(algorithms.AES(self.key), modes.CBC(self.iv)).encryptor()
        return enc.update(_pkcs7_pad(plain)) + enc.finalize()

    def _aes_decrypt(self, cipher_bytes: bytes) -> bytes:
        dec = Cipher(algorithms.AES(self.key), modes.CBC(self.iv)).decryptor()
        return _pkcs7_unpad(dec.update(cipher_bytes) + dec.finalize())

    # ---- decrypt (inbound) ----
    def decrypt_text(self, encrypt: str, msg_signature: str, timestamp: str, nonce: str) -> str:
        """Verify signature, decrypt a base64 <Encrypt> blob, return inner text."""
        expected = message_signature(self.token, timestamp, nonce, encrypt)
        if expected != msg_signature:
            raise WXCryptError("signature mismatch")
        plain = self._aes_decrypt(base64.b64decode(encrypt))
        content = plain[16:]
        if len(content) < 4:
            raise WXCryptError("plaintext too short")
        msg_len = struct.unpack(">I", content[:4])[0]
        if 4 + msg_len > len(content):
            raise WXCryptError("declared length exceeds payload")
        msg = content[4 : 4 + msg_len]
        receive_id = content[4 + msg_len :].decode(errors="ignore")
        if self.receive_id and receive_id != self.receive_id:
            raise WXCryptError("receive_id mismatch")
        return msg.decode()

    def decrypt_message(self, xml_body: str, msg_signature: str, timestamp: str, nonce: str) -> str:
        """Decrypt a full encrypted callback body (extracts <Encrypt> first)."""
        return self.decrypt_text(extract_encrypt(xml_body), msg_signature, timestamp, nonce)

    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        """URL-verification handshake: return the decrypted echostr plaintext."""
        return self.decrypt_text(echostr, msg_signature, timestamp, nonce)

    # ---- encrypt (outbound / passive reply) ----
    def encrypt_message(
        self, reply_xml: str, nonce: str, timestamp: str | None = None
    ) -> str:
        """Wrap a plaintext reply into an encrypted callback response envelope."""
        timestamp = timestamp or str(int(time.time()))
        msg = reply_xml.encode()
        payload = os.urandom(16) + struct.pack(">I", len(msg)) + msg + self.receive_id.encode()
        encrypt = base64.b64encode(self._aes_encrypt(payload)).decode()
        sign = message_signature(self.token, timestamp, nonce, encrypt)
        return (
            "<xml>"
            f"<Encrypt><![CDATA[{encrypt}]]></Encrypt>"
            f"<MsgSignature><![CDATA[{sign}]]></MsgSignature>"
            f"<TimeStamp>{timestamp}</TimeStamp>"
            f"<Nonce><![CDATA[{nonce}]]></Nonce>"
            "</xml>"
        )
