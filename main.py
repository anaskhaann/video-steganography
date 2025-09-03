from decode_video import decode_from_video
from encoder import encode_on_frames

if __name__ == "__main__":
    # Encode Message
    encode_on_frames(
        "Sample.mp4", "stego.avi", "1234", target_frames=[10, 20, 30, 40, 50, 60]
    )

    # Decode the message
    print("=== Video Decoding ===")
    msg_video = decode_from_video("stego.avi", target_frames=[10, 20, 30, 40, 50, 60])
    print("Message (Video):", msg_video)
