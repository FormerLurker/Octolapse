/*
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
##################################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see the following:
# https://github.com/FormerLurker/Octolapse/blob/master/LICENSE
#
# You can contact the author either through the git-hub repository, or at the
# following email address: FormerLurker@pm.me
##################################################################################
*/
$(function() {
    WatermarkImage = function(filepath) {
        var self = this;
        // The full file path on the OctoPrint server.
        self.filepath = filepath;

        // Returns just the filename portion from a full filepath.
        self.getFilename = function() {
            // Function stolen from https://stackoverflow.com/a/25221100.
            return self.filepath.split('\\').pop().split('/').pop();
        };
    };

    Font = function(filepath) {
        var self = this;
        // The full file path on the OctoPrint server.
        self.filepath = filepath;

        // Returns just the filename portion from a full filepath.
        self.getFilename = function() {
            // Function stolen from https://stackoverflow.com/a/25221100.
            return self.filepath.split('\\').pop().split('/').pop();
        };
    };

    Octolapse.RenderingProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Render")
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.enabled = ko.observable(values.enabled);
        self.fps_calculation_type = ko.observable(values.fps_calculation_type);
        self.run_length_seconds = ko.observable(values.run_length_seconds);
        self.fps = ko.observable(values.fps);
        self.max_fps = ko.observable(values.max_fps);
        self.min_fps = ko.observable(values.min_fps);
        self.output_format = ko.observable(values.output_format);
        self.sync_with_timelapse = ko.observable(values.sync_with_timelapse);
        self.bitrate = ko.observable(values.bitrate);
        self.post_roll_seconds = ko.observable(values.post_roll_seconds);
        self.pre_roll_seconds = ko.observable(values.pre_roll_seconds);
        self.output_template = ko.observable(values.output_template);
        self.enable_watermark = ko.observable(values.enable_watermark);
        self.selected_watermark = ko.observable(values.selected_watermark); // Absolute filepath of the selected watermark.
        self.watermark_list = ko.observableArray(); // A list of WatermarkImages that are available for selection on the server.
        self.overlay_text_template = ko.observable(values.overlay_text_template);
        self.font_list = ko.observableArray(); // A list of Fonts that are available for selection on the server.
        self.overlay_font_path = ko.observable(values.overlay_font_path);
        self.overlay_font_size = ko.observable(values.overlay_font_size);
        // Text position as a JSON string.
        self.overlay_text_pos = ko.pureComputed({
            read: function() {
                var x = +self.overlay_text_pos_x();
                var y = +self.overlay_text_pos_y();
                // Validate x and y.
                // Ensure they are integers.
                if (self.overlay_text_pos_x().length == 0 || x % 1 != 0 || self.overlay_text_pos_y().length == 0 || y % 1 != 0) {
                    return "";
                }

                return JSON.stringify([x, y]);
            },
            write: function(value) {
                if (value === undefined) {
                    return;
                }
                xy = JSON.parse(value);
                self.overlay_text_pos_x(xy[0]);
                self.overlay_text_pos_y(xy[1]);
            },
        });
        self.overlay_text_pos_x = values.overlay_text_pos_x === undefined ? ko.observable() : ko.observable(values.overlay_text_pos_x);
        self.overlay_text_pos_y = values.overlay_text_pos_y === undefined ? ko.observable() : ko.observable(values.overlay_text_pos_y);
        self.overlay_text_pos(values.overlay_text_pos);
        self.overlay_text_alignment = ko.observable(values.overlay_text_alignment);
        self.overlay_text_valign = ko.observable(values.overlay_text_valign);
        self.overlay_text_halign = ko.observable(values.overlay_text_halign);
        // The overlay text colour in as a 4-element array, represented in a string. Note values vary from 0-255.
        // ie. [57, 64, 32, 25]
        self.overlay_text_color = ko.observable(values.overlay_text_color);
        // The overlay text color formatted as a CSS value. Note RGB vary from 0-255, but A varies from 0-1.
        // ie. rgba(57, 64, 32, 0.1).
        self.overlay_text_color_as_css = ko.pureComputed({
            read: function () {
                // Convert to js.
                var rgba = JSON.parse(self.overlay_text_color());
                // Divide alpha by 255.
                rgba[3] = rgba[3] / 255;
                // Build the correct string.
                return 'rgba(' + rgba.join(', ') + ')'
            },
            write: function (value) {
                // Extract values.
                var rgba = /rgba\((\d+),\s*(\d+),\s*(\d+),\s(\d*\.?\d+)\)/.exec(value).slice(1).map(Number);
                // Multiply alpha by 255 and round.
                rgba[3] = Math.round(rgba[3] * 255);
                // Write to variable.
                self.overlay_text_color(JSON.stringify(rgba));
            },
        });

        self.overlay_preview_image = ko.observable('');
        self.overlay_preview_image_error = ko.observable('');
        self.thread_count = ko.observable(values.thread_count)
        self.overlay_preview_image_src = ko.computed(function() {
            return 'data:image/jpeg;base64,' + self.overlay_preview_image();
        });
        self.overlay_preview_image_alt_text = ko.computed(function() {
            if (self.overlay_preview_image_error.length == 0) {
                return 'A preview of the overlay text.'
            }
            return 'Image could not be retrieved from server. The error returned was: ' + self.overlay_preview_image_error() + '.';
        });

        self.can_synchronize_format = ko.pureComputed(function() {
           return ['mp4','h264'].indexOf(self.output_format()) > -1;
        });

        // This function is called when the Edit Profile dialog shows.
        self.onShow = function() {
             $('#overlay_color').minicolors({format: 'rgb', opacity: true});
             self.updateWatermarkList();
             self.updateFontList();
             self.initWatermarkUploadButton();
             self.requestOverlayPreview();

        };

        self.selectWatermark = function(watermark_image) {
            if (watermark_image === undefined) {
                self.enable_watermark(false);
                self.selected_watermark("");
                return;
            }
            self.enable_watermark(true);
            self.selected_watermark(watermark_image.filepath);
        };

        self.deleteWatermark = function(watermarkImage, event) {
            OctoPrint.postJson(OctoPrint.getBlueprintUrl('octolapse') +
                'rendering/watermark/delete', {'path': watermarkImage.filepath}, {'Content-Type':'application/json'})
                    .then(function(response) {
                        // Deselect the watermark if we just deleted the selected watermark.
                        if (self.selected_watermark() == watermarkImage.filepath) {
                            self.selectWatermark();
                        }
                        self.updateWatermarkList();
                    }, function(response) {
                        // TODO: Display error message in UI.
                        //console.log("Failed to delete " + watermarkImage.filepath);
                        //console.log(response);
                    });
            event.stopPropagation();
        };

        // Load watermark list from server-side Octolapse directory.
        self.updateWatermarkList = function() {

             return OctoPrint.get(OctoPrint.getBlueprintUrl('octolapse') +
                'rendering/watermark')
                    .then(function(response) {
                        self.watermark_list.removeAll()
                        // The let format is not working in some versions of safari
                        for (var index = 0; index < response['filepaths'].length;index++) {
                            self.watermark_list.push(new WatermarkImage(response['filepaths'][index]));
                        }
                     }, function(response) {
                        self.watermark_list.removeAll()
                        // Hacky solution, but good enough. We shouldn't encounter this error too much anyways.
                        self.watermark_list.push(new WatermarkImage("Failed to load watermarks from Octolapse data directory."));
                     });
        };

        self.initWatermarkUploadButton = function() {
             // Set up the file upload button.
             var $watermarkUploadElement = $('#octolapse_watermark_path_upload');
             var $progressBarContainer = $('#octolapse-upload-watermark-progress');
             var $progressBar = $progressBarContainer.find('.progress-bar');

             $watermarkUploadElement.fileupload({
                dataType: "json",
                maxNumberOfFiles: 1,
                headers: OctoPrint.getRequestHeaders(),
                // Need to chunk large image files or else OctoPrint/Flask will reject them.
                // TODO: Octoprint limits file upload size on a per-endpoint basis.
                // http://docs.octoprint.org/en/master/plugins/hooks.html#octoprint-server-http-bodysize
                maxChunkSize: 100000,
                progressall: function (e, data) {
                    // TODO: Get a better progress bar implementation.
                    var progress = parseInt(data.loaded / data.total * 100, 10);
                    $progressBar.text(progress + "%");
                    $progressBar.animate({'width': progress + '%'}, {'queue':false});
                },
                done: function(e, data) {
                    $progressBar.text("Done!");
                    $progressBar.animate({'width': '100%'}, {'queue':false});
                    self.updateWatermarkList().then(function() {
                        // Find the new watermark in the list and select it.
                        var matchingWatermarks = [];
                        // The lambda version was not working in safari
                        for(var index=0;index<self.watermark_list();index++)
                        {
                            if(data.files[0] == self.watermark_list()[index].getFilename())
                                matchingWatermarks.push(self.watermark_list()[index]);
                        }
                        //var matchingWatermarks = self.watermark_list().filter(w=>w.getFilename() == data.files[0].name);
                        if (matchingWatermarks.length == 0) {
                            //console.log("Error: No matching watermarks found!");
                            return
                        }
                        if (matchingWatermarks > 1){
                            //console.log("Error: More than one matching watermark found! Selecting best guess.");
                        }
                        self.selectWatermark(matchingWatermarks[0]);
                    });
                },
                fail: function(e, data) {
                    $progressBar.text("Failed...").addClass('failed');
                    $progressBar.animate({'width': '100%'}, {'queue':false});
                }
             });
        };

        // Load font list from server-side.
        self.updateFontList = function() {
             return OctoPrint.get(OctoPrint.getBlueprintUrl('octolapse') + 'rendering/font')
                    .then(function(response) {
                        self.font_list.removeAll();
                        // The let expression was not working in safari
                        for (var index = 0; index< response.length; index++) {
                            self.font_list.push(new Font(response[index]));
                        }
                     }, function(response) {
                        // Failed to load any fonts.
                        self.font_list.removeAll();
                     });
        };

        // Select a specific font for the overlay.
        self.selectOverlayFont = function(font) {
            self.overlay_font_path(font.filepath);
        };

        // Request a preview of the overlay from the server.
        self.requestOverlayPreview = function() {
            data = {
                    'overlay_text_template': self.overlay_text_template(),
                    'overlay_font_path': self.overlay_font_path(),
                    'overlay_font_size': self.overlay_font_size(),
                    'overlay_text_pos': self.overlay_text_pos(),
                    'overlay_text_alignment': self.overlay_text_alignment(),
                    'overlay_text_valign': self.overlay_text_valign(),
                    'overlay_text_halign': self.overlay_text_halign(),
                    'overlay_text_color': self.overlay_text_color(),
            };
            OctoPrint.post(OctoPrint.getBlueprintUrl('octolapse') + 'rendering/previewOverlay', data)
                .then(function(response, success_name, response_status) {
                    // Loaded the overlay!
                    self.overlay_preview_image(response.image);
                    self.overlay_preview_image_error('');
                },
                function(response_status, error_name, stack_trace) {
                    // Failed to load an overlay.
                    //console.log('Failed to load overlay preview from server.')
                    //console.log(stack_trace);
                    self.overlay_preview_image('');
                    self.overlay_preview_image_error('Error loading overlay preview: ' + error_name + '. Click to refresh.');
                });
        };

        self.toJS = function()
        {
            var copy = ko.toJS(self);
            delete copy.font_list;
            delete copy.overlay_preview_image;
            delete copy.overlay_preview_image_src;
            return copy;
        };
    };
    Octolapse.RenderingProfileValidationRules = {
        rules: {
            bitrate: { required: true, ffmpegBitRate: true },
            output_format : {required: true},
            fps_calculation_type: {required: true},
            min_fps: { lessThanOrEqual: '#rendering_profile_max_fps' },
            max_fps: { greaterThanOrEqual: '#rendering_profile_min_fps' },
            overlay_text_valign: {required: true},
            overlay_text_halign: {required: true},
            overlay_text_alignment: {required: true},
            output_template: {
                remote: {
                    url: "./plugin/octolapse/validateRenderingTemplate",
                    type:"post"
                }
            },
            overlay_text_template: {
                remote: {
                    url: "./plugin/octolapse/validateOverlayTextTemplate",
                    type:"post"
                }
            },
            octolapse_overlay_font_size: { required: true, integerPositive: true },
            octolapse_overlay_text_pos: { required: true },
        },
        messages: {
            name: "Please enter a name for your profile",
            min_fps: { lessThanOrEqual: 'Must be less than or equal to the maximum fps.' },
            max_fps: { greaterThanOrEqual: 'Must be greater than or equal to the minimum fps.' },
            output_template: { octolapseRenderingTemplate: 'Either there is an invalid token in the rendering template, or the resulting file name is not valid.' },
            overlay_text_template: { octolapseOverlayTextTemplate: 'Either there is an invalid token in the overlay text template, or the resulting file name is not valid.' },
            octolapse_overlay_text_pos: { required: 'Position offsets must be valid integers.' },
        }
    };
});


