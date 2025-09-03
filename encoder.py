import json
import os
import struct

import cv2
import numpy as np

from bits_bytes import bytes_to_bits


def encode_on_frames(video_in, video_out, message, target_frames):
    """Video frames mein message hide karta hai"""
    cap = cv2.VideoCapture(video_in)
    w, h = int(cap.get(3)), int(cap.get(4))
    fps = cap.get(5)
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Check  ki target frames exist karte hain ya nahi
    valid_target_frames = [f for f in target_frames if f < total_video_frames]
    if len(valid_target_frames) != len(target_frames):
        print(f"Warning: Some frames out of range. Using: {valid_target_frames}")
    target_frames = sorted(valid_target_frames)

    if len(target_frames) == 0:
        print("Error: No valid frames")
        cap.release()
        return

    # Message ko bytes mein convert  aur length add
    data = message.encode("utf-8")
    prefix = struct.pack(">I", len(data))
    payload_bits = bytes_to_bits(prefix + data)

    length_bits = payload_bits[:32]  # Pehle 32 bits message length ke liye
    message_bits = payload_bits[32:]  # Baaki bits actual message ke liye

    # Message bits ko remaining frames mein distribute
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
                # Pehle frame mein length bits hide
                nbits = 32
                chunk = length_bits
            else:
                # Baaki frames mein message bits hide
                nbits = min(chunk_size, len(message_bits) - bit_idx)
                chunk = message_bits[bit_idx : bit_idx + nbits]
                bit_idx += nbits
            # LSB mein bits hide
            blue[:nbits] = (blue[:nbits] & 0xFE) | chunk
            frame[:, :, 0] = blue.reshape(h, w)

        # Frame ko PNG format mein save  (lossless)
        cv2.imwrite(f"{output_dir}/frame_{frame_idx:06d}.png", frame)
        # Video file mein bhi write
        video_writer.write(frame)

        frame_idx += 1
        success, frame = cap.read()

    cap.release()
    video_writer.release()

    # Metadata save
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
