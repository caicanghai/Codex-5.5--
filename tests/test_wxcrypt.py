"""WXBizMsgCrypt: encrypt -> decrypt round trip, signatures, and error paths.

No network — this fully verifies the AES scheme used for WeChat OA / WeCom
encrypted callbacks.
"""

import base64
import os

import pytest

from app.messaging.wxcrypt import (
    WXBizMsgCrypt,
    WXCryptError,
    extract_encrypt,
    message_signature,
)

# A valid 43-char EncodingAESKey (base64 of 32 random bytes, trailing '=' dropped).
AES_KEY = base64.b64encode(os.urandom(32)).decode()[:43]
TOKEN = "eios-token"
RECEIVE_ID = "wwCorpId123"


def _crypter(receive_id: str = RECEIVE_ID) -> WXBizMsgCrypt:
    return WXBizMsgCrypt(TOKEN, AES_KEY, receive_id)


def test_encrypt_decrypt_round_trip():
    c = _crypter()
    inner = "<xml><Content><![CDATA[晚上好]]></Content></xml>"
    envelope = c.encrypt_message(inner, nonce="nonce123", timestamp="1700000000")
    encrypt = extract_encrypt(envelope)
    sig = message_signature(TOKEN, "1700000000", "nonce123", encrypt)
    out = c.decrypt_text(encrypt, sig, "1700000000", "nonce123")
    assert out == inner


def test_decrypt_message_from_full_body():
    c = _crypter()
    envelope = c.encrypt_message("hello", nonce="n", timestamp="123")
    encrypt = extract_encrypt(envelope)
    sig = message_signature(TOKEN, "123", "n", encrypt)
    assert c.decrypt_message(envelope, sig, "123", "n") == "hello"


def test_signature_mismatch_rejected():
    c = _crypter()
    envelope = c.encrypt_message("hi", nonce="n", timestamp="123")
    encrypt = extract_encrypt(envelope)
    with pytest.raises(WXCryptError):
        c.decrypt_text(encrypt, "deadbeef", "123", "n")


def test_receive_id_mismatch_rejected():
    sender = _crypter(RECEIVE_ID)
    envelope = sender.encrypt_message("hi", nonce="n", timestamp="123")
    encrypt = extract_encrypt(envelope)
    sig = message_signature(TOKEN, "123", "n", encrypt)
    wrong = _crypter("someOtherCorp")
    with pytest.raises(WXCryptError):
        wrong.decrypt_text(encrypt, sig, "123", "n")


def test_verify_url_returns_plaintext():
    c = _crypter()
    envelope = c.encrypt_message("echo-me", nonce="n", timestamp="123")
    echostr = extract_encrypt(envelope)
    sig = message_signature(TOKEN, "123", "n", echostr)
    assert c.verify_url(sig, "123", "n", echostr) == "echo-me"


def test_bad_aes_key_length_rejected():
    with pytest.raises(WXCryptError):
        WXBizMsgCrypt(TOKEN, "tooshort", RECEIVE_ID)
