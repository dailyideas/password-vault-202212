from __future__ import annotations

from Crypto.Cipher import ChaCha20


class CipherHelper:
    KEY_NUM_BYTES = 32
    NONCE_NUM_BYTES = 12
    BYTE_ORDER = "big"
    VERSION = 1
    VERSION_BYTE = VERSION.to_bytes(1, byteorder=BYTE_ORDER, signed=False)

    @classmethod
    def encrypt(cls, key: bytes, nonce: bytes, plaintext: bytes) -> bytes:
        assert (
            len(key) == cls.KEY_NUM_BYTES and len(nonce) == cls.NONCE_NUM_BYTES
        )
        cipher = ChaCha20.new(key=key, nonce=nonce)
        ciphertext = cipher.encrypt(plaintext)
        return ciphertext

    @classmethod
    def decrypt(cls, key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
        assert (
            len(key) == cls.KEY_NUM_BYTES and len(nonce) == cls.NONCE_NUM_BYTES
        )
        cipher = ChaCha20.new(key=key, nonce=nonce)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext

    @classmethod
    def encrypt_and_pack(
        cls, data: bytes, key: bytes, nonce: bytes | int
    ) -> bytes:
        if isinstance(nonce, int):
            nonce = nonce.to_bytes(
                cls.NONCE_NUM_BYTES, byteorder=cls.BYTE_ORDER, signed=False
            )
        encrypted_data = cls.encrypt(key=key, nonce=nonce, plaintext=data)
        return cls._pack_data(
            version=cls.VERSION_BYTE, nonce=nonce, data=encrypted_data
        )

    @classmethod
    def unpack_and_decrypt(cls, packed_data: bytes, key: bytes):
        nonce, ciphertext = cls._unpack_data(packed_data)
        decrypted_data = cls.decrypt(
            key=key, nonce=nonce, ciphertext=ciphertext
        )
        return decrypted_data

    @classmethod
    def _pack_data(cls, version: bytes, nonce: bytes, data: bytes):
        return version + nonce + data

    @classmethod
    def _unpack_data(cls, packed_data: bytes):
        """
        Return
        ----
        str: nonce
        str: ciphertext
        """
        version = packed_data[:1]
        if version != cls.VERSION_BYTE:
            packed_data = cls._upgrade_packed_data(packed_data)
        nonce_end_idx = 1 + cls.NONCE_NUM_BYTES
        return (
            packed_data[1:nonce_end_idx],
            packed_data[nonce_end_idx:],
        )

    @classmethod
    def _upgrade_packed_data(cls, packed_data: bytes):
        version = packed_data[:1]
        raise NotImplementedError(
            f"Cannot upgrade {cls.__name__} v{version} to v{cls.VERSION}."
        )
