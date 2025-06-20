/*
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
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
        self.data = ko.observable();
        self.profileTypeName = ko.observable("Rendering");
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
        self.bitrate = ko.observable(values.bitrate);
        self.constant_rate_factor = ko.observable(values.constant_rate_factor);
        self.post_roll_seconds = ko.observable(values.post_roll_seconds);
        self.pre_roll_seconds = ko.observable(values.pre_roll_seconds);
        self.output_template = ko.observable(values.output_template);
        self.enable_watermark = ko.observable(values.enable_watermark);
        self.selected_watermark = ko.observable(values.selected_watermark); // Absolute filepath of the selected watermark.
        self.watermark_list = ko.observableArray(); // A list of WatermarkImages that are available for selection on the server.
        self.overlay_text_template = ko.observable(values.overlay_text_template);
        self.overlay_font_path = ko.observable(values.overlay_font_path);
        self.overlay_font_size = ko.observable(values.overlay_font_size);
        self.archive_snapshots = ko.observable(values.archive_snapshots);
        self.thread_count = ko.observable(values.thread_count);
        self.data.font_list = ko.observableArray(); // A list of Fonts that are available for selection on the server.
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
                try {
                    var positions = JSON.parse(value);
                    self.overlay_text_pos_x(positions[0]);
                    self.overlay_text_pos_y(positions[1]);
                }
                catch(exc)
                {
                    self.overlay_text_pos_x(0);
                    self.overlay_text_pos_y(0);
                }

            },
        });
        self.overlay_text_pos_x = ko.observable();
        self.overlay_text_pos_y = ko.observable();
        self.overlay_text_pos(values.overlay_text_pos);
        self.overlay_text_alignment = ko.observable(values.overlay_text_alignment);
        self.overlay_text_valign = ko.observable(values.overlay_text_valign);
        self.overlay_text_halign = ko.observable(values.overlay_text_halign);
        self.overlay_text_color = ko.observable(values.overlay_text_color);
        self.overlay_outline_color = ko.observable(values.overlay_outline_color);
        self.overlay_outline_width = ko.observable(values.overlay_outline_width);

        self.text_color_to_css = function(text_color){
            // Convert to js.
            var rgba;
            if (Array.isArray(text_color))
            {
                rgba = text_color;
                // Divide alpha by 255.
                //rgba[3] = rgba[3] / 255.0;
            }
            else
            {
                rgba = JSON.parse(text_color);
            }
            // Build the correct string.
            return 'rgba(' + rgba.join(', ') + ')';
        };

        self.css_to_text_color = function(css){
            // Extract values.
                var rgba = /rgba\((\d+),\s*(\d+),\s*(\d+),\s(\d*\.?\d+)\)/.exec(css).slice(1).map(Number);
                // Multiply alpha by 255 and round.
                //rgba[3] = Math.round(rgba[3] * 255);
                // Write to variable.
                return JSON.stringify(rgba);
        };

        self.overlay_text_color_as_css = ko.pureComputed({
            read: function () {
                return self.text_color_to_css(self.overlay_text_color());
            },
            write: function (value) {
                // Extract values.
                self.overlay_text_color(self.css_to_text_color(value));
            },
        });

        self.overlay_outline_color_as_css = ko.pureComputed({
            read: function () {
                return self.text_color_to_css(self.overlay_outline_color());
            },
            write: function (value) {
                // Extract values.
                self.overlay_outline_color(self.css_to_text_color(value));
            },
        });

        self.data.overlay_preview_image = ko.observable('');
        self.data.overlay_preview_image_error = ko.observable('');
        self.data.overlay_preview_image_src = ko.computed(function() {
            return 'data:image/jpeg;base64,' + self.data.overlay_preview_image();
        });
        self.overlay_preview_image_alt_text = ko.computed(function() {
            if (self.data.overlay_preview_image_error.length == 0) {
                return 'A preview of the overlay text.';
            }
            return 'Image could not be retrieved from server. The error returned was: ' + self.data.overlay_preview_image_error() + '.';
        });

        // This function is called when the Edit Profile dialog shows.
        self.onShow = function(parent) {
             $('#octolapse_rendering_overlay_color').minicolors({format: 'rgb', opacity: true});
             $('#octolapse_rendering_outline_color').minicolors({format: 'rgb', opacity: true});
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
                        var watermarks = [];
                        for (var index = 0; index < response['filepaths'].length;index++) {
                            watermarks.push(new WatermarkImage(response['filepaths'][index]));
                        }
                        self.watermark_list(watermarks);
                     }, function(response) {
                        var watermarks = [new WatermarkImage("Failed to load watermarks from Octolapse data directory.")];
                        // Hacky solution, but good enough. We shouldn't encounter this error too much anyways.
                        self.watermark_list(watermarks);
                     });
        };

        self.initWatermarkUploadButton = function() {
             // Set up the file upload button.
             var $watermarkUploadElement = $('#octolapse_rendering_watermark_path_upload');
             var $progressBarContainer = $('#octolapse_rendering_upload_watermark_progress');
             var $progressBar = $progressBarContainer.find('.progress-bar');

             $watermarkUploadElement.fileupload({
                dataType: "json",
                maxNumberOfFiles: 1,
                headers: OctoPrint.getRequestHeaders(),
                // Need to chunk large image files or else OctoPrint/Flask will reject them.
                // TODO: Monitor issue with chunking and re-add when it is fixed.
                //maxChunkSize: 1000000,
                 maxFilesize: 10,
                 start: function(e) {
                    $progressBar.text("Starting...");
                    $progressBar.animate({'width': '0'}, {'queue': false}).removeClass('failed');
                },
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
                            return;
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
                        var server_fonts = response.fonts;
                        var font_list = [];

                        // The let expression was not working in safari
                        for (var index = 0; index< server_fonts.length; index++) {
                            font_list.push(new Font(server_fonts[index]));
                        }
                        self.data.font_list(font_list);
                     }, function(response) {
                        // Failed to load any fonts.
                        self.data.font_list.removeAll();
                     });
        };

        // Select a specific font for the overlay.
        self.selectOverlayFont = function(font) {
            self.overlay_font_path(font.filepath);
        };

        // Request a preview of the overlay from the server.
        self.requestOverlayPreview = function() {
            if (!self.overlay_text_template())
            {
                self.data.overlay_preview_image('');
                self.data.overlay_preview_image_error(
                    "Enter the text you wish to appear in your overlay in the 'Text' box above, and click refresh to preview the rendering overlay."
                );
                return;
            }
            if (self.overlay_font_path() === "")
            {
                self.data.overlay_preview_image('');
                self.data.overlay_preview_image_error(
                    "Choose a font from the list above, and click refresh to preview the rendering overlay."
                );
                return;
            }

            var data = {
                'overlay_text_template': self.overlay_text_template(),
                'overlay_font_path': self.overlay_font_path(),
                'overlay_font_size': self.overlay_font_size(),
                'overlay_text_pos': self.overlay_text_pos(),
                'overlay_text_alignment': self.overlay_text_alignment(),
                'overlay_text_valign': self.overlay_text_valign(),
                'overlay_text_halign': self.overlay_text_halign(),
                'overlay_text_color': self.overlay_text_color(),
                'overlay_outline_color': self.overlay_outline_color(),
                'overlay_outline_width': self.overlay_outline_width()
            };
            $.ajax({
                url: "./" + OctoPrint.getBlueprintUrl('octolapse') + 'rendering/previewOverlay',
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    self.data.overlay_preview_image(results.image);
                    self.data.overlay_preview_image_error('');
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    // Failed to load an overlay.
                    //console.log('Failed to load overlay preview from server.')
                    //console.log(stack_trace);
                    self.data.overlay_preview_image('');
                    self.data.overlay_preview_image_error('Error loading overlay preview: ' + errorThrown + '. Click to refresh.');
                }
            });
        };

        self.toJS = function()
        {
            var copy = ko.toJS(self);
            return copy;
        };

        self.updateFromServer = function(values) {
            self.name(values.name);
            self.description(values.description);
            self.enabled(values.enabled);
            self.fps_calculation_type(values.fps_calculation_type);
            self.run_length_seconds(values.run_length_seconds);
            self.fps(values.fps);
            self.max_fps(values.max_fps);
            self.min_fps(values.min_fps);
            self.output_format(values.output_format);
            self.bitrate(values.bitrate);
            // Might not be included in server profiles.  Make sure it is.
            if (typeof values.constant_rate_factor !== 'undefined')
                self.constant_rate_factor(values.constant_rate_factor);
            self.post_roll_seconds(values.post_roll_seconds);
            self.pre_roll_seconds(values.pre_roll_seconds);
            self.output_template(values.output_template);
            self.archive_snapshots(values.archive_snapshots);
            self.thread_count(values.thread_count);
            // Clear any settings that we don't want to update, unless they aren't important.
            self.overlay_text_template("");
            self.selected_watermark("");
            self.enable_watermark(false);
            self.overlay_font_path("");

        };

        self.automatic_configuration = new Octolapse.ProfileLibraryViewModel(
            values.automatic_configuration,
            Octolapse.Renderings.profileOptions.server_profiles,
            self.profileTypeName(),
            self,
            self.updateFromServer
        );

        self.toJS = function()
        {
            // need to remove the parent link from the automatic configuration to prevent a cyclic copy
            var parent = self.automatic_configuration.parent;
            self.automatic_configuration.parent = null;
            var copy = ko.toJS(self);
            self.automatic_configuration.parent = parent;
            return copy;
        };
        self.on_closed = function(){
            self.automatic_configuration.on_closed();
        };

        self.automatic_configuration.is_confirming.subscribe(function(value){
            //console.log("IsClickable" + value.toString());
            Octolapse.Renderings.setIsClickable(!value);
        });
    };
    Octolapse.RenderingProfileValidationRules = {
        rules: {
            octolapse_rendering_bitrate: { required: true, ffmpegBitRate: true },
            octolapse_rendering_output_format : {required: true},
            octolapse_rendering_fps_calculation_type: {required: true},
            octolapse_rendering_min_fps: { lessThanOrEqual: '#octolapse_rendering_max_fps' },
            octolapse_rendering_max_fps: { greaterThanOrEqual: '#octolapse_rendering_min_fps' },
            octolapse_rendering_overlay_text_valign: {required: true},
            octolapse_rendering_overlay_text_halign: {required: true},
            octolapse_rendering_overlay_text_alignment: {required: true},
            octolapse_rendering_output_template: {
                remote: {
                    url: "./plugin/octolapse/validateRenderingTemplate",
                    type:"post"
                }
            },
            octolapse_rendering_overlay_text_template: {
                remote: {
                    url: "./plugin/octolapse/validateOverlayTextTemplate",
                    type:"post"
                }

            },
            octolapse_rendering_overlay_font_size: { required: true, integerPositive: true },
            octolapse_rendering_overlay_text_pos: { required: true },
        },
        messages: {
            octolapse_rendering_name: "Please enter a name for your profile",
            octolapse_rendering_min_fps: { lessThanOrEqual: 'Must be less than or equal to the maximum fps.' },
            octolapse_rendering_max_fps: { greaterThanOrEqual: 'Must be greater than or equal to the minimum fps.' },
            octolapse_rendering_output_template: { octolapseRenderingTemplate: 'Either there is an invalid token in the rendering template, or the resulting file name is not valid.' },
            octolapse_rendering_overlay_text_template: { octolapseOverlayTextTemplate: 'Either there is an invalid token in the overlay text template, or the resulting file name is not valid.' },
            octolapse_rendering_overlay_text_pos: { required: 'Position offsets must be valid integers.' },
        }
    };
});


