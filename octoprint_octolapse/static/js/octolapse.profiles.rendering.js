/// Create our stabilizations view model
$(function() {
    Octolapse.RenderingProfileViewModel = function(values) {
        self = this
        self.name = ko.observable(values.name);
        self.guid = ko.observable(values.guid);
        self.enabled = ko.observable(values.enabled);
        self.fps_calculation_type = ko.observable(values.fps_calculation_type);
        self.run_length_seconds = ko.observable(values.run_length_seconds);
        self.fps = ko.observable(values.fps);
        self.max_fps = ko.observable(values.max_fps);
        self.min_fps = ko.observable(values.min_fps);
        self.output_format = ko.observable(values.output_format);
        self.output_filename = ko.observable(values.output_filename);
        self.output_directory = ko.observable(values.output_directory);
        self.sync_with_timelapse = ko.observable(values.sync_with_timelapse);
        self.bitrate = ko.observable(values.bitrate);
        self.flip_h = ko.observable(values.flip_h);
        self.flip_v = ko.observable(values.flip_v);
        self.rotate_90 = ko.observable(values.rotate_90);
        self.watermark = ko.observable(values.watermark);
    }
    Octolapse.RenderingProfileValidationRules = {
        rules: {
            name: "required",
            ffmpeg_path: "required",
            bitrate: "required",
            fps_calculation_type: "required",
            fps: { required:true, number: true, min: 0.0 }
        },
        messages: {
            name: "Please enter a name for your profile",
        }
    };
});


