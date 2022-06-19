import asyncio
from functools import partial
from typing import List

import depthai as dai

from robothub_sdk import App, CameraResolution, StreamType, Config, InputStream, router, Request, Response


class LanternJpegCapture(App):
    fps: int
    resolution: CameraResolution
    camera_controls: List[InputStream]
    frame_queue: asyncio.Queue

    def __init__(self):
        super().__init__()
        self.fps = 25
        self.resolution = CameraResolution.MAX_RESOLUTION
        self.frame_queue = asyncio.Queue(maxsize=5)

    def on_initialize(self, devices: List[dai.DeviceInfo]):
        self.config.add_defaults(route="/capture")
        self.camera_controls = []
        router.route(self.config.route)(self.handle_capture_frame)
        router.route("/cameras")(self.handle_list_cameras)

    def on_configuration(self, old_configuration: Config):
        router.plain.clear()
        router.dynamic.clear()
        router.route(self.config.route)(self.handle_capture_frame)
        router.route("/cameras")(self.handle_list_cameras)

    def on_setup(self, device):
        device.configure_camera(dai.CameraBoardSocket.RGB, res=self.resolution, fps=self.fps)
        self.camera_controls.append(device.streams.color_control)
        mjpeg_encoder = device.create_encoder(device.streams.color_still.output_node, fps=8, profile=dai.VideoEncoderProperties.Profile.MJPEG, quality=80)
        device.streams.create(mjpeg_encoder, mjpeg_encoder.bitstream, stream_type=StreamType.BINARY, rate=8).consume(partial(self.on_still_frame, device.id))

        # Publish video for preview in RobotHub
        # device.streams.color_video.publish()

    def on_still_frame(self, device_id: str, frame: dai.ImgFrame):
        if not self.frame_queue.full():
            self.loop.call_soon_threadsafe(self.frame_queue.put_nowait, frame)

    def handle_list_cameras(self, request: Request):
        return [{"id": device.id, "model": device.eeprom.boardName} for device in self.devices]

    async def handle_capture_frame(self, request: Request):
        device_id = request.query.get("camera", self.devices[0].id)
        for camera_control in self.camera_controls:
            if camera_control.device.id == device_id:
                ctl = dai.CameraControl()
                ctl.setCaptureStill(True)
                camera_control.send(ctl)
                try:
                    frame = await self.frame_queue.get()
                    response = Response(request, 200, frame.getData().data, {"content-type": "image/jpeg"})
                    return response
                except asyncio.TimeoutError:
                    return "Capture timed out", 503
        return "Camera not found", 404


app = LanternJpegCapture()
app.run()
