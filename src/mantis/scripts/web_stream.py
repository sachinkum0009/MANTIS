"""
Video File WebSocket Streamer
Streams a video file over WebSocket
"""

import asyncio
import base64
import cv2
from dataclasses import dataclass
import draccus
import logging
from pathlib import Path
import sys
import os
import websockets

from mantis.controller_position import ControllerPositions, InvalidControllerData
from mantis.bi_teleop import BiTeleop
from mantis.ik_planner import IkPlanner

logger = logging.getLogger("web_stream")
logging.basicConfig(level=logging.DEBUG)

URDF_PATH = Path("urdf/so_arm101.urdf")


class WebServer:
    """
    WebServer to stream images and collect controller positions.

    Minimal responsibilities:
    - manage websocket server and connected clients
    - broadcast video frames (from a file or externally provided frames)
    - parse/validate incoming controller JSON and invoke callbacks
    """

    def __init__(
        self,
        video_source: str,
        host: str,
        port: int,
        jpeg_quality: int,
        target_fps: int,
        resize_width: int,
    ):
        # Use module-level defaults when caller doesn't provide values
        self.video_source = video_source
        self.host = host
        self.port = port
        self.jpeg_quality = jpeg_quality
        self.target_fps = target_fps
        self.resize_width = resize_width

        self._clients: set = set()
        self._clients_lock = asyncio.Lock()
        self._broadcast_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()
        self._frame_queue: asyncio.Queue = asyncio.Queue(maxsize=2)
        self._controller_callbacks: list = []

        # initialize ik_planner
        self.ik_planner = IkPlanner(URDF_PATH)
        # initialize bi manual SO 101 arms
        self.bi_teleop = BiTeleop()
        self.bi_teleop.connect_robots()

    def register_controller_callback(self, callback):
        """
        Register a callback called with ControllerPositions when
        valid data arrives.

        Callback can be a normal function or an async coroutine function.
        """
        self._controller_callbacks.append(callback)

    async def _safe_send(self, client, data: str):
        try:
            await client.send(data)
        except websockets.exceptions.ConnectionClosed:
            async with self._clients_lock:
                self._clients.discard(client)

    async def _client_handler(self, websocket, path):
        async with self._clients_lock:
            self._clients.add(websocket)
        logger.info(f"Client connected from {websocket.remote_address}")

        try:
            async for message in websocket:
                try:
                    # Parse and validate controller positions
                    try:
                        cp = ControllerPositions.from_json(message)
                        if cp.left.trigger > 0.5:
                            if cp.left.trigger > 0.5 and cp.right.trigger > 0.5:
                                self.bi_teleop.send_pose(cp.left.pose, cp.right.pose)

                    except InvalidControllerData as exc:
                        print(f"Invalid controller data: {exc}")
                        continue
                    except Exception as exc:
                        print(f"Error processing message: {exc}")
                        continue

                    # Dispatch to callbacks; schedule coro callbacks without blocking
                    for cb in list(self._controller_callbacks):
                        if asyncio.iscoroutinefunction(cb):
                            asyncio.create_task(cb(cp))
                        else:
                            loop = asyncio.get_running_loop()
                            loop.run_in_executor(None, cb, cp)
                except websockets.exceptions.ConnectionClosed:
                    break
        finally:
            async with self._clients_lock:
                self._clients.discard(websocket)
            logger.info(f"Client disconnected from {websocket.remote_address}")

    async def _broadcast_loop(self):
        """
        Read frames from the configured video source and broadcast
        them to clients.
        """
        # If video_source is a path, open it with OpenCV
        if isinstance(self.video_source, str):
            if not os.path.exists(self.video_source):
                logger.error(f"Error: Video file '{self.video_source}' not found!")
                logger.error(f"Current directory: {os.getcwd()}")
                return

            cap = cv2.VideoCapture(self.video_source)

            if not cap.isOpened():
                logger.error(f"Error: Could not open video file '{self.video_source}'")
                return

            video_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            logger.info(f"Streaming on ws://{self.host}:{self.port}")
            logger.info(f"Video file: {self.video_source}")
            logger.info(f"Video FPS: {video_fps}, Total frames: {total_frames}")
            logger.info(
                f"Target FPS: {self.target_fps}, JPEG Quality: {self.jpeg_quality}%"
            )
            logger.info("Waiting for clients...")

            frame_time = 1.0 / self.target_fps
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]

            try:
                while not self._shutdown_event.is_set():
                    # Priority to externally provided frames
                    try:
                        frame = self._frame_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        ret, frame = cap.read()
                        # Loop video if we reached the end
                        if not ret:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ret, frame = cap.read()
                            if not ret:
                                logger.warning("Error: Could not read frame from video")
                                break

                    # Resize frame if needed
                    if self.resize_width:
                        height, width = frame.shape[:2]
                        if width != self.resize_width:
                            aspect_ratio = height / width
                            new_height = int(self.resize_width * aspect_ratio)
                            frame = cv2.resize(frame, (self.resize_width, new_height))

                    # Encode frame as JPEG
                    _, buffer = cv2.imencode(".jpg", frame, encode_param)
                    data = base64.b64encode(buffer.tobytes()).decode("utf-8")

                    # Broadcast to all connected clients
                    async with self._clients_lock:
                        clients = list(self._clients)

                    if clients:
                        await asyncio.gather(
                            *[self._safe_send(c, data) for c in clients]
                        )

                    # Maintain target frame rate
                    await asyncio.sleep(frame_time)

            finally:
                cap.release()
                logger.debug("Stream stopped")

        else:
            # If not a path, expect an async producer via send_frame()
            frame_time = 1.0 / self.target_fps
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            logger.info(f"Streaming on ws://{self.host}:{self.port} (external frames)")
            try:
                while not self._shutdown_event.is_set():
                    try:
                        frame = await asyncio.wait_for(
                            self._frame_queue.get(), timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        await asyncio.sleep(frame_time)
                        continue

                    # Encode frame as JPEG
                    _, buffer = cv2.imencode(".jpg", frame, encode_param)
                    data = base64.b64encode(buffer.tobytes()).decode("utf-8")

                    async with self._clients_lock:
                        clients = list(self._clients)

                    if clients:
                        await asyncio.gather(
                            *[self._safe_send(c, data) for c in clients]
                        )

            finally:
                logger.info("External stream stopped")

    async def start(self):
        """Start the websocket server and broadcasting loop (async)."""
        logger.info("Video File WebSocket Streamer")

        async with websockets.serve(self._client_handler, self.host, self.port):
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())
            await self._shutdown_event.wait()

            # Wait for broadcast task to finish
            if self._broadcast_task:
                try:
                    await self._broadcast_task
                except asyncio.CancelledError:
                    pass

    def run(self):
        """
        Convenience synchronous runner that blocks until stopped (KeyboardInterrupt).
        """
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.debug("\nShutting down...")

    def stop(self):
        """Signal the server to stop. This is safe to call from other tasks."""
        self._shutdown_event.set()

    def send_frame(self, frame):
        """Submit an externally produced frame to be broadcasted."""
        try:
            self._frame_queue.put_nowait(frame)
        except asyncio.QueueFull:
            # Drop frame if queue is full to avoid blocking the producer
            pass


@dataclass
class WebServerConfig:
    video_source: str = "test_video.mp4"
    host: str = "0.0.0.0"
    port: int = 8765
    jpeg_quality = 70
    target_fps = 30
    resize_width = 640


@draccus.wrap()
def main(cfg: WebServerConfig):
    """Construct and run the WebServer (blocking)."""
    server = WebServer(
        video_source=cfg.video_source,
        host=cfg.host,
        port=cfg.port,
        jpeg_quality=cfg.jpeg_quality,
        target_fps=cfg.target_fps,
        resize_width=cfg.resize_width,
    )
    server.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        sys.exit(0)
