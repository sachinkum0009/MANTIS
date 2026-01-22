#!/usr/bin/env python3
"""
Video File WebSocket Streamer
Streams a video file over WebSocket

Requirements:
    pip install opencv-python websockets numpy

Usage:
    python web_stream.py
"""

import cv2
import asyncio
import websockets
import base64
import sys
import numpy as np
import os

# Configuration
VIDEO_FILE = "test_video.mp4"  # Video file to stream
PORT = 8765
HOST = "0.0.0.0"  # Listen on all interfaces
JPEG_QUALITY = 70  # 1-100, lower = smaller file, lower quality
TARGET_FPS = 30
RESIZE_WIDTH = 640  # Resize to this width (maintains aspect ratio)

clients = set()


async def stream_camera(websocket):
    """Handle a single WebSocket client connection"""
    clients.add(websocket)
    print(f"Client connected from {websocket.remote_address}")

    try:
        # Receive messages from client (controller positions)
        async for message in websocket:
            try:
                # Print controller position data received from Godot
                print(f"Received from client: {message}")
            except Exception as e:
                print(f"Error processing message: {e}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        print(f"Client disconnected from {websocket.remote_address}")


async def broadcast_frames():
    """Read video file and broadcast frames to all connected clients"""
    # Check if video file exists
    if not os.path.exists(VIDEO_FILE):
        print(f"Error: Video file '{VIDEO_FILE}' not found!")
        print(f"Current directory: {os.getcwd()}")
        return

    # Open video file
    cap = cv2.VideoCapture(VIDEO_FILE)

    if not cap.isOpened():
        print(f"Error: Could not open video file '{VIDEO_FILE}'")
        return

    # Get video properties
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Streaming on ws://{HOST}:{PORT}")
    print(f"Video file: {VIDEO_FILE}")
    print(f"Video FPS: {video_fps}, Total frames: {total_frames}")
    print(f"Target FPS: {TARGET_FPS}, JPEG Quality: {JPEG_QUALITY}%")
    print("Waiting for clients...")

    frame_time = 1.0 / TARGET_FPS
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]

    try:
        while True:
            ret, frame = cap.read()

            # Loop video if we reached the end
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame from video")
                    break

            # Resize frame if needed
            if RESIZE_WIDTH:
                height, width = frame.shape[:2]
                if width != RESIZE_WIDTH:
                    aspect_ratio = height / width
                    new_height = int(RESIZE_WIDTH * aspect_ratio)
                    frame = cv2.resize(frame, (RESIZE_WIDTH, new_height))

            # Encode frame as JPEG
            _, buffer = cv2.imencode(".jpg", frame, encode_param)
            data = base64.b64encode(buffer).decode("utf-8")

            # Broadcast to all connected clients
            if clients:
                websockets_to_remove = set()
                for client in clients:
                    try:
                        await client.send(data)
                    except websockets.exceptions.ConnectionClosed:
                        websockets_to_remove.add(client)

                # Remove disconnected clients
                clients.difference_update(websockets_to_remove)

            # Maintain target frame rate
            await asyncio.sleep(frame_time)

    finally:
        cap.release()
        print("Stream stopped")


async def main():
    """Start WebSocket server and video streaming"""
    print("=" * 60)
    print("Video File WebSocket Streamer")
    print("=" * 60)

    # Start WebSocket server
    async with websockets.serve(stream_camera, HOST, PORT):
        # Start broadcasting frames
        await broadcast_frames()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
