import struct

import cv2
import numpy as np

from bits_bytes import bits_to_bytes


def decode_from_video(video_file, target_frames=None):
    """Video file se directly message extract karta hai"""
    if target_frames is None:
        return ""

    target_frames = sorted(target_frames)
    first_frame = target_frames[0]
    cap = cv2.VideoCapture(video_file)

    # First frame tak seek
    for i in range(first_frame + 1):
        success, frame = cap.read()
        if not success:
            cap.release()
            return ""

    # Message length nikalo
    blue = frame[:, :, 0].reshape(-1)
    length_bits = (blue[:32] & 1).tolist()
    length_bytes = bits_to_bytes(np.array(length_bits, dtype=np.uint8))
    (msg_len,) = struct.unpack(">I", length_bytes)

    total_bits = 32 + msg_len * 8
    message_bits_len = total_bits - 32
    num_remaining = len(target_frames) - 1
    chunk_size = (
        int(np.ceil(message_bits_len / num_remaining))
        if num_remaining > 0
        else message_bits_len
    )

    # Video reset aur saare bits collect
    cap.release()
    cap = cv2.VideoCapture(video_file)

    bits = []
    remaining_message_bits = message_bits_len
    frame_idx = 0
    success, frame = cap.read()

    while success and len(bits) < total_bits:
        if frame_idx in target_frames:
            blue = frame[:, :, 0].reshape(-1)
            if frame_idx == target_frames[0]:
                nbits = 32
                frame_bits = (blue[:nbits] & 1).tolist()
                bits.extend(frame_bits)
            else:
                nbits = min(chunk_size, remaining_message_bits)
                if nbits > 0:
                    frame_bits = (blue[:nbits] & 1).tolist()
                    bits.extend(frame_bits)
                    remaining_message_bits -= nbits
        frame_idx += 1
        success, frame = cap.read()

    cap.release()

    if len(bits) < total_bits:
        return ""

    # Message extract
    msg_bits = bits[32:]
    if len(msg_bits) > 0:
        message = bits_to_bytes(np.array(msg_bits, dtype=np.uint8))
        return message.decode("utf-8", errors="ignore")
    else:
        return ""
