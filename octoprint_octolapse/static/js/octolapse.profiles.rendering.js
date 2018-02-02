/// Create our stabilizations view model
$(function() {
    Octolapse.RenderingProfileViewModel = function(values) {
        var self = this;
        self.name = ko.observable(values.name);
        self.guid = ko.observable(values.guid);
        self.enabled = ko.observable(values.enabled);
        self.fps_calculation_type = ko.observable(values.fps_calculation_type);
        self.run_length_seconds = ko.observable(values.run_length_seconds);
        self.fps = ko.observable(values.fps);
        self.max_fps = ko.observable(values.max_fps);
        self.min_fps = ko.observable(values.min_fps);
        self.output_format = ko.observable(values.output_format);
        self.sync_with_timelapse = ko.observable(values.sync_with_timelapse);
        self.bitrate = ko.observable(values.bitrate);
        self.flip_h = ko.observable(values.flip_h);
        self.flip_v = ko.observable(values.flip_v);
        self.rotate_90 = ko.observable(values.rotate_90);
        self.watermark = ko.observable(values.watermark);
        self.post_roll_seconds = ko.observable(values.post_roll_seconds);
        self.pre_roll_seconds = ko.observable(values.pre_roll_seconds);
        
    }
    Octolapse.RenderingProfileValidationRules = {
        rules: {
            bitrate: { required: true, ffmpegBitRate: true },
            min_fps: { lessThanOrEqual: '#octolapse_rendering_max_fps' },
            max_fps: { greaterThanOrEqual: '#octolapse_rendering_min_fps' },
        },
        messages: {
            name: "Please enter a name for your profile",
            min_fps: { lessThanOrEqual: 'Must be less than or equal to the maximum fps.' },
            max_fps: { greaterThanOrEqual: 'Must be greater than or equal to the minimum fps.' },
        }
    };
});


