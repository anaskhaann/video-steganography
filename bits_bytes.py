import numpy as np


def bytes_to_bits(data: bytes) -> np.ndarray:
    """Bytes ko bits mein convert karta hai"""
    arr = np.frombuffer(data, dtype=np.uint8)
    bits = ((arr[:, None] >> np.arange(7, -1, -1)) & 1).astype(np.uint8)
    return bits.reshape(-1)


def bits_to_bytes(bits: np.ndarray) -> bytes:
    """Bits ko wapas bytes mein convert karta hai"""
    bits = bits[: (bits.size // 8) * 8].reshape(-1, 8)
    return np.packbits(bits, axis=1, bitorder="big").reshape(-1).tobytes()
