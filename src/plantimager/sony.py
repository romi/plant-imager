#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# plantimager - Python tools for the ROMI 3D Plant Imager
#
# Copyright (C) 2018 Sony Computer Science Laboratories
# Authors: D. Colliaux, T. Wintz, P. Hanappe
#
# This file is part of plantimager.
#
# plantimager is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# plantimager is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with plantimager.  If not, see
# <https://www.gnu.org/licenses/>.

import json
import os
import subprocess
import tempfile
import time
from io import BytesIO

import imageio
import numpy as np
import requests

from plantimager.error import FlashAirAPIError
from plantimager.error import SonyCamError
from plantimager.hal import AbstractCamera
from plantimager.hal import DataItem
from plantimager.units import time_s
from romitask.log import get_logger

logger = get_logger(__name__)

CAMERA_FUNCTION_SHOOT = 'Remote Shooting'
CAMERA_FUNCTION_TRANSFER = 'Contents Transfer'


class SonyCamAPI(object):
    """High‑level Python wrapper for Sony Camera HTTP API.

    This class abstracts the low‑level JSON‑RPC calls required to control a
    Sony camera over the network. It provides convenience methods for common
    actions such as starting recording mode, taking a picture, querying status,
    and transferring images via ADB.

    Attributes
    ----------
    device_ip : str
        Stored IP address of the camera.
    api_port : str
        Stored API port.
    api_url : str
        Base URL built from ``device_ip`` and ``api_port``.
    timeout : float
        Timeout used for ``requests.post`` calls.
    supported_methods : list of str
        List of method names supported by the camera, retrieved during
        initialization via ``get_method_types``.
    """

    def __init__(self, device_ip, api_port, timeout=2):
        """Constructor.

        Parameters
        ----------
        device_ip : str
            IP address of the camera (e.g., ``'192.168.1.10'``).
        api_port : str
            Port on which the camera's API service is listening (usually ``'80'``).
        timeout : float, optional, default ``2.0``
            Network timeout in seconds for each HTTP request.
        """
        self.device_ip = device_ip
        self.api_port = api_port
        self.api_url = 'http://' + device_ip + ':' + api_port + '/sony/'
        self.timeout = timeout
        method_types = self.get_method_types()
        self.supported_methods = [x[0] for x in method_types]

    def api_call(self, endpoint, method, params=[], version='1.0'):
        """Perform a JSON‑RPC call to the Sony camera.

        Parameters
        ----------
        endpoint : str
            API endpoint (e.g., ``'camera'`` or ``'avContent'``).
        method : str
            Remote method name to invoke.
        params : list, optional, default ``[]``
            Positional parameters for the remote method.
        version : str, optional, default ``'1.0'``
            API version string.

        Returns
        -------
        list or dict
            The ``'result'`` or ``'results'`` field from the JSON response.
            Returns an empty ``dict`` if the response contains neither.

        Raises
        ------
        SonyCamError
            If the remote API returns an ``'error'`` field.

        Notes
        -----
        The method serialises ``params`` to JSON and sends a POST request.
        It decodes the response as UTF‑8 before parsing.
        """
        request_result = requests.post(self.api_url + endpoint,
                                       data=json.dumps({
                                           'method': method,
                                           'params': params,
                                           'id': 1,
                                           'version': version
                                       }),
                                       timeout=self.timeout)
        res = json.loads(request_result.content.decode('utf-8'))
        if 'error' in res:
            err = res['error']
            raise SonyCamError('''
            Failed camera request.
            Exception code: %d
            Description: %s
            ''' % (err[0], err[1]))
        if 'result' in res:
            return res['result']
        if 'results' in res:
            return res['results']
        return {}

    def start_rec_mode(self):
        """Switch the camera to recording mode.

        Returns
        -------
        list
            The raw result returned by the ``startRecMode`` API call.

        Raises
        ------
        SonyCamError
            Propagated from :meth:`api_call` if the request fails.
        """
        return self.api_call("camera", "startRecMode")

    def take_picture(self):
        """Capture a single still image.

        The method polls the camera status until it becomes ``'IDLE'``.
        If the camera is in ``'ContentsTransfer'`` mode, a `SonyCamError` is raised.

        Returns
        -------
        str
            URL or file identifier of the captured picture (first element of the API ``actTakePicture`` result).

        Raises
        ------
        SonyCamError
            If the camera is in content‑transfer mode or if the request fails.
        """
        while True:
            status = self.get_camera_status()
            if status == 'ContentsTransfer':
                raise SonyCamError('Camera is in content transfer mode, cannot take picture')
            elif status == 'IDLE':
                break
            else:
                time.sleep(0.1)

        return self.api_call("camera", "actTakePicture")[0]

    def get_available_camera_function(self) -> list[str]:
        """Retrieve the list of camera functions supported by the device."""
        return self.api_call("camera", "getAvailableCameraFunction")[0]

    def get_camera_function(self) -> str:
        """Get the currently selected camera function."""
        return self.api_call("camera", "getCameraFunction")[0]

    def set_camera_function(self, function) -> str:
        """Set the active camera function.

        Parameters
        ----------
        function : str
            Desired camera function (e.g., ``'still'`` or ``'movie'``).

        Returns
        -------
        str
            Confirmation string returned by the API.
        """
        return self.api_call("camera", "setCameraFunction", [function])[0]

    def get_storage_information(self) -> dict:
        """Query storage details such as free space and total capacity.

        Returns
        -------
        dict
            Storage information dictionary as defined by the Sony API.
        """
        return self.api_call("camera", "getStorageInformation")[0]

    def get_source_list(self) -> list[dict]:
        """Retrieve a list of available storage sources.

        Returns
        -------
        list of dict
            Each entry describes a storage source (e.g., ``{'scheme': 'storage', ...}``).
        """
        return self.api_call("avContent", "getSourceList", [{"scheme": "storage"}])[0]

    def get_content_list(self, count, uri, stIdx=0, view="flat", sort="descending") -> list[dict]:
        """List media content under a specific ``uri``.

        Parameters
        ----------
        count : int
            Maximum number of items to return.
        uri : str
            Base URI of the content container (e.g., ``'storage:memory'``).
        stIdx : int, optional, default ``0``
            Starting index for pagination.
        view : str, optional, default ``'flat'``
            View mode; ``'flat'`` returns a flat list.
        sort : str, optional, default ``'descending'``
            Sort order of results.

        Returns
        -------
        list of dict
            Content entries matching the query.
        """
        return self.api_call("avContent", "getContentList", [{
            "uri": uri,
            "stIdx": stIdx,
            "cnt": count,
            "view": view,
            "sort": sort}], version="1.3")[0]

    def get_camera_status(self) -> str:
        """Obtain the current camera status from the event stream.

        Returns
        -------
        str
            Status string such as ``'IDLE'``, ``'ContentsTransfer'``, etc.

        Raises
        ------
        SonyCamError
            If the status cannot be extracted from the event list.
        """
        events = self.get_event()
        for x in events:
            if 'cameraStatus' in x:
                return x['cameraStatus']
        raise SonyCamError('Could not get camera status')

    def get_available_api_list(self) -> list[str]:
        """List all API categories supported by the camera.

        Returns
        -------
        list of str
            API categories (e.g., ``['camera', 'avContent']``).
        """
        return self.api_call("camera", "getAvailableApiList")[0]

    def get_method_types(self, version="1.0") -> list[tuple[str, str]]:
        """Retrieve supported method names and their signatures.

        Parameters
        ----------
        version : str, optional, default ``'1.0'``
            API version for the ``getMethodTypes`` call.

        Returns
        -------
        list of tuple
            Each tuple contains ``(method_name, method_type)``.
        """
        return self.api_call("camera", "getMethodTypes", [version])

    def get_event(self, long_polling=False, version="1.0"):
        """Poll the camera for events.

        Parameters
        ----------
        long_polling : bool, optional, default ``False``
            If ``True``, the call blocks until an event occurs.
        version : str, optional, default ``'1.0'``
            API version for the ``getEvent`` request.

        Returns
        -------
        list of dict
            Event dictionaries returned by the camera.
        """
        return self.api_call("camera", "getEvent", [long_polling], version=version)

    def start_shoot_mode(self):
        """Prepare the camera for still‑image shooting.

        This method ensures the camera function is set to shooting mode and switches to recording mode if required.
        It blocks until the camera reports ``'IDLE'`` status.

        Raises
        ------
        SonyCamError
            Propagated from underlying API calls.
        """
        if ('setCameraFunction' in self.supported_methods and
                'getCameraFunction' in self.supported_methods):
            camera_function = self.get_camera_function()
            if camera_function != CAMERA_FUNCTION_SHOOT:
                self.set_camera_function(CAMERA_FUNCTION_SHOOT)
        if 'startRecMode' in self.supported_methods:
            self.start_rec_mode()
        while not self.get_camera_status() == 'IDLE':
            continue

    def setup_camera(self, params) -> None:
        """Configure multiple camera settings in a single call.

        Parameters
        ----------
        params : dict
            Mapping of setting names to desired values. Recognised keys are:
            ``'FNumber'``, ``'ShutterSpeed'``, ``'IsoSpeedRate'``,
            ``'WhiteBalance'``, ``'FlashMode'``, ``'FocusMode'``.
        """
        if 'FNumber' in params:
            self.api_call('camera', 'setFNumber', [params['FNumber']])
        if 'ShutterSpeed' in params:
            self.api_call('camera', 'setShutterSpeed', [params['ShutterSpeed']])
        if 'IsoSpeedRate' in params:
            self.api_call('camera', 'setIsoSpeedRate', [params['IsoSpeedRate']])
        if 'WhiteBalance' in params:
            self.api_call('camera', 'setWhiteBalance', [params['WhiteBalance']])
        if 'FlashMode' in params:
            self.api_call('camera', 'setFlashMode', [params['FlashMode']])
        if 'FocusMode' in params:
            self.api_call('camera', 'setFocusMode', [params['FocusMode']])

    def start_transfer_mode(self):
        """Switch the camera to ``'ContentsTransfer'`` mode for bulk download.

        The method sets the camera function to transfer mode (if supported) and
        blocks until the device reports ``'ContentsTransfer'`` status.

        Raises
        ------
        SonyCamError
            Propagated from underlying API calls.
        """
        if ('setCameraFunction' in self.supported_methods and
                'getCameraFunction' in self.supported_methods):
            camera_function = self.get_camera_function()
            if camera_function != CAMERA_FUNCTION_TRANSFER:
                self.set_camera_function(CAMERA_FUNCTION_TRANSFER)
        while not self.get_camera_status() == 'ContentsTransfer':
            continue

    def get_available_shoot_mode(self) -> list[str]:
        """Return the list of supported shoot modes.

        Returns
        -------
        list of str
            Available shoot modes (e.g., ``['still', 'movie']``)."""
        return self.api_call("camera", "getAvailableShootMode")[1]

    def set_shoot_mode(self, mode) -> str:
        """Change the current shoot mode.

        Parameters
        ----------
        mode : str
            Desired shoot mode identifier (must be one of the values returned by `get_available_shoot_mode`).

        Returns
        -------
        str
            Confirmation string from the camera.
        """
        return self.api_call("camera", "setShootMode", [mode])

    def start_movie_rec(self):
        """Begin video recording.

        Returns
        -------
        list
            Result payload from the ``startMovieRec`` API call.
        """
        return self.api_call("camera", "startMovieRec")

    def stop_movie_rec(self):
        """Stop an ongoing video recording.

        Returns
        -------
        list
            Result payload from the ``stopMovieRec`` API call.
        """
        return self.api_call("camera", "stopMovieRec")

    def adb_transfer_pictures(self, count=1):
        """Transfer the latest ``count`` pictures from the camera via ADB.

        Parameters
        ----------
        count : int, optional, default ``1``
            Number of most‑recent images to pull.

        Returns
        -------
        list of numpy.ndarray
            Loaded images as NumPy arrays.

        Notes
        -----
        - ADB shell must be enabled on the camera.
        - Images are temporarily stored in ``/tmp/`` before being read with ``imageio.imread``.
        - The method prints each filename as it is transferred.
        """
        # Connect (ignore "already connected" noise)
        try:
            subprocess.run(
                ["adb", "connect", self.device_ip],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to connect to device {self.device_ip}") from exc

        # List files sorted by modification time (using `ls -t`)
        result = subprocess.run(
            ["adb", "shell", "ls", "-t", "/sdcard/DCIM/100MSDCF"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        files = files[:count]  # newest first

        images: list[np.ndarray] = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            for f in files:
                # Pull safely
                subprocess.run(
                    ["adb", "pull", f"/sdcard/DCIM/100MSDCF/{f}", tmp_dir],
                    check=True,
                    timeout=30,
                )
                img_path = os.path.join(tmp_dir, f)
                images.append(imageio.imread(img_path))
                logger.info("Pulled %s", f)

        return images


class FlashAirAPI(object):
    def __init__(self, host):
        self.host = host
        self.commands_format = "http://%s/command.cgi?%s"
        self.delete_format = "http://%s/upload.cgi?DEL=%s"
        self.path_format = "http://%s%s"
        requests.get(self.path_format % (self.host, "/"))

    def format_datetime(self, date, time):
        return date + time  # TODO

    def format_attribute(self, attribute):
        return attribute  # TODO

    def get_file_list(self, path):
        res = requests.get(self.commands_format % (self.host, "op=100&DIR=%s" % path))
        res = res.content.split()
        # print(res)
        if res[0] != b'WLANSD_FILELIST':
            raise FlashAirAPIError("Could not retrieve file list")

        files = []
        for i in range(1, len(res)):
            directory, fname, size, attribute, date, time = res[i].decode().split(',')
            datetime = self.format_datetime(date, time)
            attribute = self.format_attribute(attribute)
            files.append({
                "directory": directory,
                "filename": fname,
                "size": size,
                "attribute": attribute,
                "datetime": datetime,
            })
        return files

    def transfer_latest_pictures(self, count=1, tmpdir=None):
        dir_list = self.get_file_list('/DCIM')
        files = []
        for x in dir_list:
            if x['filename'] != '100__TSB':  # Ignore file from SD card
                files.extend(self.get_file_list('/DCIM/' + x['filename']))

        files.sort(key=lambda x: x['filename'], reverse=True)  # TODO: sort by date
        images = []
        fnames = []
        for i in range(count):
            if i >= len(files):
                break
            path = '%s/%s' % (files[i]['directory'], files[i]['filename'])
            url = self.path_format % (self.host, path)
            print(url)
            new_image = imageio.imread(BytesIO(requests.get(url).content), format='jpg')
            if not (tmpdir):
                images.append(new_image)
            else:
                # print(files[i]['filename'])
                fname = os.path.join(tmpdir, files[i]['filename'])
                imageio.imwrite(fname, new_image)
                fnames.append(fname)

        if not (tmpdir):
            return images[::-1]
        else:
            return fnames

    def delete_all(self):
        files = []
        dir_list = self.get_file_list('/DCIM')
        for x in dir_list:
            if x['filename'] != '100__TSB':  # Ignore file from SD card
                files.extend(self.get_file_list('/DCIM/' + x['filename']))

        for f in files:
            requests.get(self.delete_format % (self.host, f['directory'] + '/' + f['filename']))


class Camera(AbstractCamera):
    """Sony Remote Control API.

    Provides a high‑level interface to a Sony camera over the network, allowing image capture and optional
    post‑processing such as rotation.
    Images are returned as `plantimager.hal.DataItem` objects with an ``rgb`` channel containing a NumPy array.

    Attributes
    ----------
    sony_cam : SonyCamAPI
        Low‑level API wrapper handling direct camera communication.
    postview : bool
        Flag indicating whether postview mode is active.
    use_adb : bool
        Flag indicating whether ADB transfer is used.
    use_flashair : bool
        Flag indicating whether FlashAir transfer is used.
    flashair : FlashAirAPI, optional
        Instance of `~plantimager.sony.FlashAirAPI` when
        ``use_flashair`` is ``True``.
    camera_params : dict or None
        Camera configuration dictionary passed to `SonyCamAPI.setup_camera`.
    rotation : int
        Rotation angle (degrees counter‑clockwise) applied to images.

    Raises
    ------
    SonyCamError
        If both ``use_flashair`` and ``use_adb`` are ``True`` or if
        ``use_flashair`` is ``True`` but ``flashair_host`` is not provided.

    See Also
    --------
    SonyCamAPI : Low‑level API for Sony camera commands.
    FlashAirAPI : API for interacting with a FlashAir Wi‑Fi SD card.

    Examples
    --------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> from plantimager.sony import Camera
    >>> # Capture a low‑resolution image using postview mode (Sony RX0):
    >>> cam = Camera('192.168.122.1', '10000', postview=True, rotation=0)
    >>> img = cam.grab(0)
    >>> arr = img.channels['rgb'].data
    >>> print(arr.shape)
    (1440, 1080, 3)
    >>> # Visualize the capture image:
    >>> plt.imshow(arr)
    >>> plt.show()

    >>> # Capture a rotated low‑resolution image using postview mode (Sony RX0):
    >>> cam = Camera('192.168.122.1', '10000', postview=True, rotation=270)
    >>> img = cam.grab(0)
    >>> arr = np.array(img.channels['rgb'].data)
    >>> print(arr.shape)
    (1080, 1440, 3)
    >>> # Visualize the capture image:
    >>> plt.imshow(arr)
    >>> plt.show()
    """

    def __init__(self, device_ip: str,
                 api_port: str,
                 timeout: time_s = 10,
                 postview: bool = False,
                 use_adb: bool = False,
                 use_flashair: bool = False,
                 flashair_host: str = None,
                 camera_params: dict = None,
                 rotation: int = 0):
        """Constructor.

        Parameters
        ----------
        device_ip : str
            IP address of the Sony camera.
        api_port : str
            Port number of the camera's API endpoint.
        timeout : time_s, optional
            Network timeout (in seconds) for API calls. Default is ``10``.
        postview : bool, optional
            If ``True``, download the low‑resolution postview image directly from the camera.
            ``False`` uses a full‑resolution download path.
        use_adb : bool, optional
            Use Android Debug Bridge (ADB) to transfer the picture.
            Mutually exclusive with ``use_flashair``.
        use_flashair : bool, optional
            Use a Wi‑Fi SD card (FlashAir) to transfer the picture.
            Mutually exclusive with ``use_adb``.
        flashair_host : str, optional
            Host IP of the FlashAir device. Required when ``use_flashair`` is ``True``.
        camera_params : dict, optional
            Dictionary of camera settings that are applied after entering shoot mode.
        rotation : int, optional
            Counter‑clockwise rotation (in degrees) applied to the captured image.
            Only multiples of 90° are supported; other values are reduced modulo 360.
        """
        self.sony_cam = SonyCamAPI(device_ip, api_port, timeout=timeout)
        self.postview = postview
        self.use_flashair = use_flashair
        self.use_adb = use_adb
        if use_flashair and use_adb:
            raise SonyCamError("Cannot use both flashair and adb for transfer")
        if use_flashair:
            if flashair_host is None:
                raise SonyCamError("Must provide flashair host IP")
            self.flashair = FlashAirAPI(flashair_host)

        self.camera_params = camera_params
        self.rotation = rotation  # degrees counter-clockwise
        self.start()

    def start(self):
        """Initialize the camera for shooting.

        Raises
        ------
        SonyCamError
            If the camera cannot be switched to shoot mode or if a configuration command fails.
        """
        self.sony_cam.start_shoot_mode()
        self.sony_cam.set_shoot_mode("still")
        if self.camera_params is not None:
            self.sony_cam.setup_camera(self.camera_params)

    def channels(self):
        return ['rgb']

    def grab(self, idx: int, metadata: dict = None) -> DataItem:
        """Capture a single image from the Sony camera.

        Parameters
        ----------
        idx : int
            Index assigned to the returned `~plantimager.hal.DataItem`.
            Useful for sequencing images when multiple captures are performed.
        metadata : dict, optional
            Arbitrary user‑defined metadata that will be attached to the resulting `~plantimager.hal.DataItem`.
            If ``None`` an empty metadata dictionary is created.

        Returns
        -------
        DataItem
            A data container with an ``rgb`` channel holding the captured image as a NumPy ``ndarray``.
            The channel can be accessed via ``item.channels['rgb'].data``.

        Raises
        ------
        SonyCamError
            * If both ``use_adb`` and ``use_flashair`` are enabled (checked at construction time).
            * If the camera is in a state that prevents picture capture (e.g., ``ContentsTransfer`` mode).
            * If any network request (HTTP or ADB) fails.

        Notes
        -----
        * The method chooses the image transfer mechanism in the following priority order:
            1. **Postview** – low‑resolution image retrieved directly from the camera URL.
            2. **ADB** – uses Android Debug Bridge to pull the latest image from the camera’s internal storage.
            3. **FlashAir** – pulls the latest image from a Wi‑Fi SD card.
            4. **File‑transfer mode** – switches the camera to *Contents Transfer* mode and downloads the
               full‑resolution image via HTTP.
        * If ``rotation`` is non‑zero, the image is rotated counter‑clockwise in multiples of 90°.
        """
        data_item = DataItem(idx, metadata)
        res = self.sony_cam.take_picture()
        url = res[0]
        if self.postview:  # Download image from postview
            data = imageio.imread(BytesIO(requests.get(url).content))
        elif self.use_adb:  # Download using android debug
            images = self.sony_cam.adb_transfer_pictures(count=1)
            data = images[0]
        elif self.use_flashair:  # Download on wifi sd card
            images = self.flashair.transfer_latest_pictures(count=1)
            data = images[0]
        else:  # Download using file transfer mode (not available on all cameras)
            self.sony_cam.start_transfer_mode()
            uri = self.sony_cam.get_source_list()[0]['source']
            content_list = self.sony_cam.get_content_list(count=1, uri=uri)
            content = content_list[0]
            content = content['content']['original'][0]
            url = content['url']
            data = imageio.imread(BytesIO(requests.get(url).content))
            self.sony_cam.start_shoot_mode()

        if self.rotation != 0:
            # Rotate using NumPy for multiples of 90 degrees (counter‑clockwise)
            # k = number of 90° rotations
            k = (self.rotation // 90) % 4
            data = np.rot90(data, k=k)

        data_item.add_channel('rgb', data)
        return data_item
