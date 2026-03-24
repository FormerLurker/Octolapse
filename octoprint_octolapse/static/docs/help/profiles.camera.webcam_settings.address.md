This is the full path to the web camera.  This address can be used in the Snapshot Address and the Camera Settings Request Templates by using the {camera_address} replacement token.

The initial setting (after install or after you restore the default settings) is based on the OctoPrint settings within the 'Webcam & Timelapse' screen.  The OctoPrint default is (I believe) ```http://127.0.0.1:8080/```

For Yawcam the default port is 8888, so if you haven't changed that and as long as your Yawcam instance is running on the same computer as OctoPrint, you should be able to use this as your base address:  ```http://127.0.0.1:8888/```

Notice that there is a trailing / on the address.  This is important if you want to take advantage of some of the default settings (and you probably do).

If you are using a remote camera, that will work too as long as you enter the proper URL, and that the URL you are using is accessible from the host computer.  If you are using HTTPS without a trusted certificate or a username/password, please see the advanced camera profile settings at the very bottom of the profile screen.
