import json
import os
import struct

import cv2
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


def encode_on_frames(video_in, video_out, message, target_frames):
    """Video frames mein message hide karta hai"""
    cap = cv2.VideoCapture(video_in)
    w, h = int(cap.get(3)), int(cap.get(4))
    fps = cap.get(5)
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Check karo ki target frames exist karte hain ya nahi
    valid_target_frames = [f for f in target_frames if f < total_video_frames]
    if len(valid_target_frames) != len(target_frames):
        print(f"Warning: Some frames out of range. Using: {valid_target_frames}")
    target_frames = sorted(valid_target_frames)

    if len(target_frames) == 0:
        print("Error: No valid frames")
        cap.release()
        return

    # Message ko bytes mein convert karo aur length add karo
    data = message.encode("utf-8")
    prefix = struct.pack(">I", len(data))
    payload_bits = bytes_to_bits(prefix + data)

    length_bits = payload_bits[:32]  # Pehle 32 bits message length ke liye
    message_bits = payload_bits[32:]  # Baaki bits actual message ke liye

    # Message bits ko remaining frames mein distribute karo
    num_remaining = len(target_frames) - 1
    if num_remaining > 0:
        chunk_size = int(np.ceil(len(message_bits) / num_remaining))
    else:
        chunk_size = len(message_bits)

    # Output directory banao PNG frames ke liye
    output_dir = video_out.replace(".avi", "_frames")
    os.makedirs(output_dir, exist_ok=True)

    # Video file bhi banao lossless codec ke saath
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")
    video_writer = cv2.VideoWriter(video_out, fourcc, fps, (w, h))

    bit_idx = 0
    frame_idx = 0
    success, frame = cap.read()
    while success:
        if frame_idx in target_frames:
            blue = frame[:, :, 0].reshape(-1)  # Blue channel nikalo
            if frame_idx == target_frames[0]:
                # Pehle frame mein length bits hide karo
                nbits = 32
                chunk = length_bits
            else:
                # Baaki frames mein message bits hide karo
                nbits = min(chunk_size, len(message_bits) - bit_idx)
                chunk = message_bits[bit_idx : bit_idx + nbits]
                bit_idx += nbits
            # LSB mein bits hide karo
            blue[:nbits] = (blue[:nbits] & 0xFE) | chunk
            frame[:, :, 0] = blue.reshape(h, w)

        # Frame ko PNG format mein save karo (lossless)
        cv2.imwrite(f"{output_dir}/frame_{frame_idx:06d}.png", frame)
        # Video file mein bhi write karo
        video_writer.write(frame)

        frame_idx += 1
        success, frame = cap.read()

    cap.release()
    video_writer.release()

    # Metadata save karo
    metadata = {
        "total_frames": frame_idx,
        "target_frames": target_frames,
        "fps": fps,
        "width": w,
        "height": h,
    }
    with open(f"{output_dir}/metadata.json", "w") as f:
        json.dump(metadata, f)

    print("Message successfully encoded!")
    print(f"Video: {video_out}")


def decode_from_frames(frames_dir, target_frames=None):
    """PNG frames se message extract karta hai"""
    if target_frames is None:
        return ""

    target_frames = sorted(target_frames)
    first_frame = target_frames[0]

    # Pehla frame load karo message length nikalne ke liye
    frame_path = f"{frames_dir}/frame_{first_frame:06d}.png"
    if not os.path.exists(frame_path):
        return ""

    frame = cv2.imread(frame_path)

    # Blue channel se length bits nikalo
    blue = frame[:, :, 0].reshape(-1)
    length_bits = (blue[:32] & 1).tolist()
    length_bytes = bits_to_bytes(np.array(length_bits, dtype=np.uint8))
    (msg_len,) = struct.unpack(">I", length_bytes)

    # Total bits calculate karo
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

    # Har target frame se bits collect karo
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

    # Message bits extract karo (length skip karke)
    msg_bits = bits[32:]
    if len(msg_bits) > 0:
        message = bits_to_bytes(np.array(msg_bits, dtype=np.uint8))
        return message.decode("utf-8", errors="ignore")
    else:
        return ""


def decode_from_video(video_file, target_frames=None):
    """Video file se directly message extract karta hai"""
    if target_frames is None:
        return ""

    target_frames = sorted(target_frames)
    first_frame = target_frames[0]
    cap = cv2.VideoCapture(video_file)

    # First frame tak seek karo
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

    # Video reset karo aur saare bits collect karo
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

    # Message extract karo
    msg_bits = bits[32:]
    if len(msg_bits) > 0:
        message = bits_to_bytes(np.array(msg_bits, dtype=np.uint8))
        return message.decode("utf-8", errors="ignore")
    else:
        return ""


# Video mein message encode karo
encode_on_frames(
    "Sample.mp4", "stego.avi", "1234", target_frames=[10, 20, 30, 40, 50, 60]
)

# PNG frames se decode karo (sabse reliable)
print("\n=== PNG Frames se Decoding ===")
msg_png = decode_from_frames("stego_frames", target_frames=[10, 20, 30, 40, 50, 60])
print("Message (PNG):", msg_png)

# Video file se decode karo (test karne ke liye)
print("\n=== Video File se Decoding ===")
msg_video = decode_from_video("stego.avi", target_frames=[10, 20, 30, 40, 50, 60])
print("Message (Video):", msg_video)
