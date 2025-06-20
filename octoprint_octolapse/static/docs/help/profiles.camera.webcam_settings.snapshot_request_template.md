You can either enter the full path for your webcam's snapshot page, or you can use the {camera_address} template.  Using the {camera_address} token is preferred if for no other reason than to verify that the base address is correct.  The base address is used for custom image preferences as well as some error checking, and it's important that you get it correct.

The default value is ```{camera_address}?action=snapshot```, which works well for mjpg_streamer (bundled with octopi).  If you are using Yawcam you probably want to use ```{camera_address}out.jpg```

The default full url after replacing the {camera_address} token with the default 'Base Address' above would be would be ```http://127.0.0.1:8080/?action=snapshot``` for mjpg_streamer and ```http://127.0.0.1:8888/out.jpg``` for Yawcam.

If the 'Test' button does not work, you can also enter a full snapshot url here.  If the URL works in a browser window and returns a JPEG image, it will likely work in Octolapse.
