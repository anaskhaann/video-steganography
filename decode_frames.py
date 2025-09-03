import os
import struct

import cv2
import numpy as np

from bits_bytes import bits_to_bytes


def decode_from_frames(frames_dir, target_frames=None):
    """PNG frames se message extract karta hai"""
    if target_frames is None:
        return ""

    target_frames = sorted(target_frames)
    first_frame = target_frames[0]

    # Pehla frame load  message length nikalne ke liye
    frame_path = f"{frames_dir}/frame_{first_frame:06d}.png"
    if not os.path.exists(frame_path):
        return ""

    frame = cv2.imread(frame_path)

    # Blue channel se length bits nikalo
    blue = frame[:, :, 0].reshape(-1)
    length_bits = (blue[:32] & 1).tolist()
    length_bytes = bits_to_bytes(np.array(length_bits, dtype=np.uint8))
    (msg_len,) = struct.unpack(">I", length_bytes)

    # Total bits calculate
    total_bits = 32 + msg_len * 8
    message_bits_len = total_bits - 32
    num_remaining = len(target_frames) - 1
    chunk_size = (
        int(np.ceil(message_bits_len / num_remaining))
        if num_remaining > 0
        else message_bits_len
    )

    bits = []
    remaining_message_bits = message_bits_len

    # Har target frame se bits collect
    for frame_idx in target_frames:
        frame_path = f"{frames_dir}/frame_{frame_idx:06d}.png"
        if not os.path.exists(frame_path):
            continue

        frame = cv2.imread(frame_path)
        blue = frame[:, :, 0].reshape(-1)

        if frame_idx == target_frames[0]:
            # Pehle frame se length bits
            nbits = 32
            frame_bits = (blue[:nbits] & 1).tolist()
            bits.extend(frame_bits)
        else:
            # Baaki frames se message bits
            nbits = min(chunk_size, remaining_message_bits)
            if nbits > 0:
                frame_bits = (blue[:nbits] & 1).tolist()
                bits.extend(frame_bits)
                remaining_message_bits -= nbits

    if len(bits) < total_bits:
        return ""

    # Message bits extract  (length skip karke)
    msg_bits = bits[32:]
    if len(msg_bits) > 0:
        message = bits_to_bytes(np.array(msg_bits, dtype=np.uint8))
        return message.decode("utf-8", errors="ignore")
    else:
        return ""
