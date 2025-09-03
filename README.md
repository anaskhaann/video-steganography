# Video Steganography Tool 🎥🔒

A Python-based steganography tool that hides secret messages in video files using LSB (Least Significant Bit) manipulation in the blue channel of specific frames.

## 🚀 Features

- **Frame-based Encoding**: Hide messages in specific video frames for better security
- **Dual Output**: Creates both lossless PNG frames and video files
- **Reliable Decoding**: Supports decoding from both PNG frames and video files
- **Smart Frame Validation**: Automatically validates target frames against video length
- **Lossless Storage**: Uses PNG format for guaranteed bit-perfect storage

## 🛠️ Installation

1. Clone the repository:

```bash
git clone https://github.com/anaskhaann/video-steganography.git
cd video-steganography
```

2. Install dependencies:

```bash
uv add opencv-python numpy
```

3. Or Simply Run:

```bash
uv sync
```

## 📖 How It Works

The tool uses LSB (Least Significant Bit) steganography in the blue channel of video frames:

1. **Message Encoding**:

   - Converts message to binary format with length prefix
   - Distributes bits across specified target frames
   - First frame stores message length (32 bits)
   - Remaining frames store message data

2. **Frame Selection**:

   - Uses specific frame numbers for encoding/decoding
   - Ensures frames exist within video length
   - Maintains consistent order for reliable extraction

3. **Dual Storage**:
   - Saves individual frames as PNG (lossless)
   - Creates video file with FFV1 codec (lossless)

## 🎯 Usage

### Basic Example

```python
from main import encode_on_frames, decode_from_frames, decode_from_video

# Encode message in video
encode_on_frames(
    video_in="input.mp4",
    video_out="stego.avi",
    message="Secret Message",
    target_frames=[10, 20, 30, 40, 50, 60]
)

# Decode from PNG frames (most reliable)
message = decode_from_frames(
    frames_dir="stego_frames",
    target_frames=[10, 20, 30, 40, 50, 60]
)

# Decode from video file
message = decode_from_video(
    video_file="stego.avi",
    target_frames=[10, 20, 30, 40, 50, 60]
)
```

### Running the Demo

```bash
python main.py
```

This will:

1. Encode "Anas" in `Sample.mp4`
2. Create `stego.avi` and `stego_frames/` directory
3. Decode message using both methods
4. Display results

## 📁 Output Structure

```
project/
├── Sample.mp4          # Original video
├── stego.avi          # Encoded video
├── stego_frames/      # PNG frames directory
│   ├── frame_000000.png
│   ├── frame_000001.png
│   ├── ...
│   └── metadata.json  # Frame metadata
└── main.py            # Main script
```

## 🔧 Functions

### Core Functions

- `bytes_to_bits(data)` - Convert bytes to binary array
- `bits_to_bytes(bits)` - Convert binary array back to bytes
- `encode_on_frames()` - Hide message in video frames
- `decode_from_frames()` - Extract message from PNG frames
- `decode_from_video()` - Extract message from video file

### Parameters

- `video_in`: Input video file path
- `video_out`: Output video file path
- `message`: Text message to hide
- `target_frames`: List of frame numbers to use
- `frames_dir`: Directory containing PNG frames

## ⚡ Performance Tips

1. **Frame Selection**: Use frames that exist in your video (check frame count first)
2. **Message Size**: Longer messages require more frames or larger frames
3. **Codec Choice**: FFV1 provides lossless compression for video output
4. **Reliability**: PNG frames offer 100% reliability, video files may have minor compression

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ by Mohd Anas
