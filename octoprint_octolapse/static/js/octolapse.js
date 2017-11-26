$(function () {
    function OctolapseSettingsViewModel(parameters) {
        var self = this;
        self.global_settings = parameters[0];

        self.is_octolapse_enabled = ko.observable();

        self.current_printer_guid = ko.observable();
        self.printers = ko.observableArray();
        self.newPrinterNumber = 0;

        self.current_stabilization_guid = ko.observable();
        self.stabilizations = ko.observableArray();
        self.newStabilizationNumber = 0;

        self.current_snapshot_guid = ko.observable();
        self.snapshots = ko.observableArray();
        self.newSnapshotNumber = 0;

        self.current_rendering_guid = ko.observable();
        self.renderings = ko.observableArray();
        self.newRenderingNumber = 0;

        self.current_camera_guid = ko.observable();
        self.cameras = ko.observableArray();
        self.newCameraNumber = 0;

        self.default_printer = ko.observable();
        
        self.default_stabilization = ko.observable();
        self.default_snapshot = ko.observable();
        self.default_rendering = ko.observable();
        self.default_camera = ko.observable();
        

        self.onBeforeBinding = function () {
            self.settings = self.global_settings.settings.plugins.octolapse;

            self.is_octolapse_enabled(self.settings.is_octolapse_enabled);
            self.current_printer_guid(self.settings.current_printer_guid);
            self.current_stabilization_guid(self.settings.current_stabilization_guid);
            self.current_snapshot_guid(self.settings.current_snapshot_guid);
            self.current_rendering_guid(self.settings.current_rendering_guid);
            self.current_camera_guid(self.settings.current_camera_guid);

            self.default_printer(self.settings.default_printer);
            self.default_stabilization(self.settings.default_stabilization);
            self.default_snapshot(self.settings.default_snapshot);
            self.default_rendering(self.settings.default_rendering);
            self.default_camera(self.settings.default_camera);

            console.log(self.default_stabilization);
            self.printers(self.settings.printers);
            self.stabilizations(self.settings.stabilizations);
            self.snapshots(self.settings.snapshots);
            self.renderings(self.settings.renderings);
            self.cameras(self.settings.cameras);
        }
        self.arrayFirstIndexOf = function (array, predicate, predicateOwner) {
            for (var i = 0, j = array.length; i < j; i++) {
                if (predicate.call(predicateOwner, array[i])) {
                    return i;
                }
            }
            return -1;
        }

        self.addPrinter = function (currentPrinter) {
            self.newPrinterNumber++;
            var newGuid = "NewPrinterGuid_" + (self.newPrinterNumber);
            
            self.global_settings.settings.plugins.octolapse.printers.push({
                name: ko.observable("New Printer" +
                    + (self.newPrinterNumber)),
                guid: ko.observable(newGuid),
                retract_length: ko.observable(currentPrinter.retract_length()),
                retract_speed: ko.observable(currentPrinter.retract_speed()),
                movement_speed: ko.observable(currentPrinter.movement_speed()),
                is_e_relative: ko.observable(currentPrinter.is_e_relative()),
                z_hop: ko.observable(currentPrinter.z_hop()),
                z_min: ko.observable(currentPrinter.z_min()),
                snapshot_command: ko.observable(currentPrinter.snapshot_command())
            });
            self.settings.current_printer_guid(newGuid);
        };
        self.resetPrinter = function (definition) {
            var guid = definition.guid();
            var index = self.arrayFirstIndexOf(this.global_settings.settings.plugins.octolapse.printers(),
                function (item) {
                    return item.guid() === guid;
                });
            
            var currentPrinter = this.global_settings.settings.plugins.octolapse.printers()[index];
            var defaultPrinter = this.global_settings.settings.plugins.octolapse.default_printer;
            //Set default values
            currentPrinter.retract_length(defaultPrinter.retract_length());
            currentPrinter.retract_speed(defaultPrinter.retract_speed());
            currentPrinter.movement_speed(defaultPrinter.movement_speed());
            currentPrinter.is_e_relative(defaultPrinter.is_e_relative());
            currentPrinter.z_hop(defaultPrinter.z_hop());
            currentPrinter.z_min(defaultPrinter.z_min());
            currentPrinter.snapshot_command(defaultPrinter.snapshot_command());
        };
        self.removePrinter = function (definition) {
            
            if (self.global_settings.settings.plugins.octolapse.printers().length <= 1) {
                alert("You may not delete the last active printer");
                return;
            }
                
            self.global_settings.settings.plugins.octolapse.printers.remove(definition);
            self.global_settings.settings.plugins.octolapse.current_printer_guid(
                self.global_settings.settings.plugins.octolapse.printers()[0].guid);

        };
        
        self.addStabilization = function (currentStabilization) {
            self.newStabilizationNumber++;
            var newGuid = "NewStabilizationGuid_" + (self.newStabilizationNumber);

            self.global_settings.settings.plugins.octolapse.stabilizations.push({
                name: ko.observable("New Stabilization" +
                    + (self.newStabilizationNumber)),
                guid: ko.observable(newGuid),
                x_movement_speed: ko.observable(currentStabilization.x_movement_speed()),
                x_type: ko.observable(currentStabilization.x_type()),
                x_fixed_coordinate: ko.observable(currentStabilization.x_fixed_coordinate()),
                x_fixed_path: ko.observable(currentStabilization.x_fixed_path()),
                x_fixed_path_loop: ko.observable(currentStabilization.x_fixed_path_loop()),
                x_relative: ko.observable(currentStabilization.x_relative()),
                x_relative_print: ko.observable(currentStabilization.x_relative_print()),
                x_relative_path: ko.observable(currentStabilization.x_relative_path()),
                x_relative_path_loop: ko.observable(currentStabilization.x_relative_path_loop()),
                y_movement_speed_mms: ko.observable(currentStabilization.y_movement_speed_mms()),
                y_type: ko.observable(currentStabilization.y_type()),
                y_fixed_coordinate: ko.observable(currentStabilization.y_fixed_coordinate()),
                y_fixed_path: ko.observable(currentStabilization.y_fixed_path()),
                y_fixed_path_loop: ko.observable(currentStabilization.y_fixed_path_loop()),
                y_relative: ko.observable(currentStabilization.y_relative()),
                y_relative_print: ko.observable(currentStabilization.y_relative_print()),
                y_relative_path: ko.observable(currentStabilization.y_relative_path()),
                y_relative_path_loop: ko.observable(currentStabilization.y_relative_path_loop()),
                z_movement_speed_mms: ko.observable(currentStabilization.z_movement_speed_mms())
            });
            self.settings.current_stabilization_guid(newGuid);
        };
        self.resetStabilization = function (definition) {
            var index = self.arrayFirstIndexOf(this.global_settings.settings.plugins.octolapse.stabilizations(),
                function (item) {
                    return item.guid() === definition.guid();
                });
            console.log(index);
            var currentStabilization = this.global_settings.settings.plugins.octolapse.stabilizations()[index];
            var defaultStabilization = this.global_settings.settings.plugins.octolapse.default_stabilization;

            currentStabilization.x_movement_speed(defaultStabilization.x_movement_speed());
            currentStabilization.x_type(defaultStabilization.x_type());
            currentStabilization.x_fixed_coordinate(defaultStabilization.x_fixed_coordinate());
            currentStabilization.x_fixed_path(defaultStabilization.x_fixed_path());
            currentStabilization.x_fixed_path_loop(defaultStabilization.x_fixed_path_loop());
            currentStabilization.x_relative(defaultStabilization.x_relative());
            currentStabilization.x_relative_print(defaultStabilization.x_relative_print());
            currentStabilization.x_relative_path(defaultStabilization.x_relative_path());
            currentStabilization.x_relative_path_loop(defaultStabilization.x_relative_path_loop());
            currentStabilization.y_movement_speed_mms(defaultStabilization.y_movement_speed_mms());
            currentStabilization.y_type(defaultStabilization.y_type());
            currentStabilization.y_fixed_coordinate(defaultStabilization.y_fixed_coordinate());
            currentStabilization.y_fixed_path(defaultStabilization.y_fixed_path());
            currentStabilization.y_fixed_path_loop(defaultStabilization.y_fixed_path_loop());
            currentStabilization.y_relative(defaultStabilization.y_relative());
            currentStabilization.y_relative_print(defaultStabilization.y_relative_print());
            currentStabilization.y_relative_path(defaultStabilization.y_relative_path());
            currentStabilization.y_relative_path_loop(defaultStabilization.y_relative_path_loop());
            currentStabilization.z_movement_speed_mms(defaultStabilization.z_movement_speed_mms());

        };
        self.removeStabilization = function (definition) {
            if (self.global_settings.settings.plugins.octolapse.stabilizations().length <= 1) {
                alert("You may not delete the last active stabilization");
                return;
            }

            self.global_settings.settings.plugins.octolapse.stabilizations.remove(definition);
            self.global_settings.settings.plugins.octolapse.current_stabilization_guid(
                self.global_settings.settings.plugins.octolapse.stabilizations()[0].guid);
        };

        self.addSnapshot = function (currentSnapshot) {
            self.newSnapshotNumber++;
            var newGuid = "NewSnapshotGuid_" + (self.newSnapshotNumber);

            self.global_settings.settings.plugins.octolapse.snapshots.push({
                name: ko.observable("New Snapshot" +
                    + (self.newSnapshotNumber)),
                guid: ko.observable(newGuid),
                gcode_trigger_enabled: ko.observable(currentSnapshot.gcode_trigger_enabled()),
                gcode_trigger_require_zhop: ko.observable(currentSnapshot.gcode_trigger_require_zhop()),
                gcode_trigger_on_extruding: ko.observable(currentSnapshot.gcode_trigger_on_extruding()),
                gcode_trigger_on_extruding_start: ko.observable(currentSnapshot.gcode_trigger_on_extruding_start()),
                gcode_trigger_on_primed: ko.observable(currentSnapshot.gcode_trigger_on_primed()),
                gcode_trigger_on_retracting: ko.observable(currentSnapshot.gcode_trigger_on_retracting()),
                gcode_trigger_on_retracted: ko.observable(currentSnapshot.gcode_trigger_on_retracted()),
                gcode_trigger_on_detracting: ko.observable(currentSnapshot.gcode_trigger_on_detracting()),

                timer_trigger_enabled: ko.observable(currentSnapshot.timer_trigger_enabled()),
                timer_trigger_seconds: ko.observable(currentSnapshot.timer_trigger_seconds()),
                timer_trigger_require_zhop: ko.observable(currentSnapshot.timer_trigger_require_zhop()),
                timer_trigger_on_extruding: ko.observable(currentSnapshot.timer_trigger_on_extruding()),
                timer_trigger_on_extruding_start: ko.observable(currentSnapshot.timer_trigger_on_extruding_start()),
                timer_trigger_on_primed: ko.observable(currentSnapshot.timer_trigger_on_primed()),
                timer_trigger_on_retracting: ko.observable(currentSnapshot.timer_trigger_on_retracting()),
                timer_trigger_on_retracted: ko.observable(currentSnapshot.timer_trigger_on_retracted()),
                timer_trigger_on_detracting: ko.observable(currentSnapshot.timer_trigger_on_detracting()),

                layer_trigger_enabled: ko.observable(currentSnapshot.layer_trigger_enabled()),
                layer_trigger_height: ko.observable(currentSnapshot.layer_trigger_height()),
                layer_trigger_require_zhop: ko.observable(currentSnapshot.layer_trigger_require_zhop()),
                layer_trigger_on_extruding: ko.observable(currentSnapshot.layer_trigger_on_extruding()),
                layer_trigger_on_extruding_start: ko.observable(currentSnapshot.layer_trigger_on_extruding_start()),
                layer_trigger_on_primed: ko.observable(currentSnapshot.layer_trigger_on_primed()),
                layer_trigger_on_retracting: ko.observable(currentSnapshot.layer_trigger_on_retracting()),
                layer_trigger_on_retracted: ko.observable(currentSnapshot.layer_trigger_on_retracted()),
                layer_trigger_on_detracting: ko.observable(currentSnapshot.layer_trigger_on_detracting()),

                archive: ko.observable(currentSnapshot.archive()),
                delay: ko.observable(currentSnapshot.delay()),
                retract_before_move: ko.observable(currentSnapshot.retract_before_move()),
                output_format: ko.observable(currentSnapshot.output_format()),
                output_filename: ko.observable(currentSnapshot.output_filename()),
                output_directory: ko.observable(currentSnapshot.output_directory()),
                cleanup_before_print: ko.observable(currentSnapshot.cleanup_before_print()),
                cleanup_after_print: ko.observable(currentSnapshot.cleanup_after_print()),
                cleanup_after_cancel: ko.observable(currentSnapshot.cleanup_after_cancel()),
                cleanup_after_fail: ko.observable(currentSnapshot.cleanup_after_fail()),
                cleanup_before_close: ko.observable(currentSnapshot.cleanup_before_close()),
                cleanup_after_render_complete: ko.observable(currentSnapshot.cleanup_after_render_complete()),
                cleanup_after_render_fail: ko.observable(currentSnapshot.cleanup_after_render_fail()),
                custom_script_enabled: ko.observable(currentSnapshot.custom_script_enabled()),
                script_path: ko.observable(currentSnapshot.script_path())
            });
            self.settings.current_snapshot_guid(newGuid);
        };
        self.removeSnapshot = function (definition) {
            if (self.global_settings.settings.plugins.octolapse.snapshots().length <= 1) {
                alert("You may not delete the last active snapshot");
                return;
            }

            self.global_settings.settings.plugins.octolapse.snapshots.remove(definition);
            self.global_settings.settings.plugins.octolapse.current_snapshot_guid(
                self.global_settings.settings.plugins.octolapse.snapshots()[0].guid);
        };
        self.resetSnapshot = function (definition) {
            var index = self.arrayFirstIndexOf(this.global_settings.settings.plugins.octolapse.snapshots(),
                function (item) {
                    return item.guid() === definition.guid();
                });
            console.log(index);
            var currentSnapshot = this.global_settings.settings.plugins.octolapse.snapshots()[index];
            var defaultSnapshot = this.global_settings.settings.plugins.octolapse.default_snapshot;

            currentSnapshot.gcode_trigger_enabled(defaultSnapshot.gcode_trigger_enabled());
            currentSnapshot.gcode_trigger_require_zhop(defaultSnapshot.gcode_trigger_require_zhop());
            currentSnapshot.gcode_trigger_on_extruding(defaultSnapshot.gcode_trigger_on_extruding());
            currentSnapshot.gcode_trigger_on_extruding_start(defaultSnapshot.gcode_trigger_on_extruding_start());
            currentSnapshot.gcode_trigger_on_primed(defaultSnapshot.gcode_trigger_on_primed());
            currentSnapshot.gcode_trigger_on_retracting(defaultSnapshot.gcode_trigger_on_retracting());
            currentSnapshot.gcode_trigger_on_retracted(defaultSnapshot.gcode_trigger_on_retracted());
            currentSnapshot.gcode_trigger_on_detracting(defaultSnapshot.gcode_trigger_on_detracting());
            currentSnapshot.timer_trigger_enabled(defaultSnapshot.timer_trigger_enabled());
            currentSnapshot.timer_trigger_seconds(defaultSnapshot.timer_trigger_seconds());
            currentSnapshot.timer_trigger_require_zhop(defaultSnapshot.timer_trigger_require_zhop());
            currentSnapshot.timer_trigger_on_extruding(defaultSnapshot.timer_trigger_on_extruding());
            currentSnapshot.timer_trigger_on_extruding_start(defaultSnapshot.timer_trigger_on_extruding_start());
            currentSnapshot.timer_trigger_on_primed(defaultSnapshot.timer_trigger_on_primed());
            currentSnapshot.timer_trigger_on_retracting(defaultSnapshot.timer_trigger_on_retracting());
            currentSnapshot.timer_trigger_on_retracted(defaultSnapshot.timer_trigger_on_retracted());
            currentSnapshot.timer_trigger_on_detracting(defaultSnapshot.timer_trigger_on_detracting());
            currentSnapshot.layer_trigger_enabled(defaultSnapshot.layer_trigger_enabled());
            currentSnapshot.layer_trigger_height(defaultSnapshot.layer_trigger_height());
            currentSnapshot.layer_trigger_require_zhop(defaultSnapshot.layer_trigger_require_zhop());
            currentSnapshot.layer_trigger_on_extruding(defaultSnapshot.layer_trigger_on_extruding());
            currentSnapshot.layer_trigger_on_extruding_start(defaultSnapshot.layer_trigger_on_extruding_start());
            currentSnapshot.layer_trigger_on_primed(defaultSnapshot.layer_trigger_on_primed());
            currentSnapshot.layer_trigger_on_retracting(defaultSnapshot.layer_trigger_on_retracting());
            currentSnapshot.layer_trigger_on_retracted(defaultSnapshot.layer_trigger_on_retracted());
            currentSnapshot.layer_trigger_on_detracting(defaultSnapshot.layer_trigger_on_detracting());

            currentSnapshot.archive(defaultSnapshot.archive());
            currentSnapshot.delay(defaultSnapshot.delay());
            currentSnapshot.retract_before_move(defaultSnapshot.retract_before_move());
            currentSnapshot.output_format(defaultSnapshot.output_format());
            currentSnapshot.output_filename(defaultSnapshot.output_filename());
            currentSnapshot.output_directory(defaultSnapshot.output_directory());
            currentSnapshot.cleanup_before_print(defaultSnapshot.cleanup_before_print());
            currentSnapshot.cleanup_after_print(defaultSnapshot.cleanup_after_print());
            currentSnapshot.cleanup_after_cancel(defaultSnapshot.cleanup_after_cancel());
            currentSnapshot.cleanup_after_fail(defaultSnapshot.cleanup_after_fail());
            currentSnapshot.cleanup_before_close(defaultSnapshot.cleanup_before_close());
            currentSnapshot.cleanup_after_render_complete(defaultSnapshot.cleanup_after_render_complete());
            currentSnapshot.cleanup_after_render_fail(defaultSnapshot.cleanup_after_render_fail());
            currentSnapshot.custom_script_enabled(defaultSnapshot.custom_script_enabled());
            currentSnapshot.script_path(defaultSnapshot.script_path());

        };

        self.addRendering = function (currentRendering) {
            self.newRenderingNumber++;
            var newGuid = "NewRenderingGuid_" + (self.newRenderingNumber);

            self.global_settings.settings.plugins.octolapse.renderings.push({
                name: ko.observable("New Rendering" +
                    + (self.newRenderingNumber)),
                guid: ko.observable(newGuid),
                enabled: ko.observable(currentRendering.enabled()),
                fps_calculation_type: ko.observable(currentRendering.fps_calculation_type()),
                run_length_seconds: ko.observable(currentRendering.run_length_seconds()),
                fps: ko.observable(currentRendering.fps()),
                max_fps: ko.observable(currentRendering.max_fps()),
                min_fps: ko.observable(currentRendering.min_fps()),
                output_format: ko.observable(currentRendering.output_format()),
                output_filename: ko.observable(currentRendering.output_filename()),
                output_directory: ko.observable(currentRendering.output_directory()),
                sync_with_timelapse: ko.observable(currentRendering.sync_with_timelapse()),
                octoprint_timelapse_directory: ko.observable(currentRendering.octoprint_timelapse_directory()),
                ffmpeg_path: ko.observable(currentRendering.ffmpeg_path()),
                bitrate: ko.observable(currentRendering.bitrate()),
                flip_h: ko.observable(currentRendering.flip_h()),
                flip_v: ko.observable(currentRendering.flip_v()),
                rotate_90: ko.observable(currentRendering.rotate_90()),
                watermark: ko.observable(currentRendering.watermark())
            });

            self.settings.current_rendering_guid(newGuid);
        };
        self.removeRendering = function (definition) {
            

            if (self.global_settings.settings.plugins.octolapse.renderings().length <= 1) {
                alert("You may not delete the last active rendering");
                return;
            }

            self.global_settings.settings.plugins.octolapse.renderings.remove(definition);
            self.global_settings.settings.plugins.octolapse.current_rendering_guid(
                self.global_settings.settings.plugins.octolapse.renderings()[0].guid);

        };

        self.resetRendering = function (definition) {
            var index = self.arrayFirstIndexOf(this.global_settings.settings.plugins.octolapse.renderings(),
                function (item) {
                    return item.guid() === definition.guid();
                });
            console.log(index);
            var currentRendering = this.global_settings.settings.plugins.octolapse.renderings()[index];
            var defaultRendering = this.global_settings.settings.plugins.octolapse.default_rendering;

            //Set default values
            currentRendering.enabled(defaultRendering.enabled());
            currentRendering.fps_calculation_type(defaultRendering.fps_calculation_type());
            currentRendering.run_length_seconds(defaultRendering.run_length_seconds());
            currentRendering.fps(defaultRendering.fps());
            currentRendering.max_fps(defaultRendering.max_fps());
            currentRendering.min_fps(defaultRendering.min_fps());
            currentRendering.output_format(defaultRendering.output_format());
            currentRendering.output_filename(defaultRendering.output_filename());
            currentRendering.output_directory(defaultRendering.output_directory());
            currentRendering.sync_with_timelapse(defaultRendering.sync_with_timelapse());
            currentRendering.octoprint_timelapse_directory(defaultRendering.octoprint_timelapse_directory());
            currentRendering.ffmpeg_path(defaultRendering.ffmpeg_path());
            currentRendering.bitrate(defaultRendering.bitrate());
            currentRendering.flip_h(defaultRendering.flip_h());
            currentRendering.flip_v(defaultRendering.flip_v());
            currentRendering.rotate_90(defaultRendering.rotate_90());
            currentRendering.watermark(defaultRendering.watermark());
            
        };

        self.addCamera = function (currentCamera) {
            self.newCameraNumber++;
            var newGuid = "NewCameraGuid_" + (self.newCameraNumber);

            self.global_settings.settings.plugins.octolapse.cameras.push({
                name: ko.observable("New Camera" +
                    + (self.newCameraNumber)),
                guid: ko.observable(newGuid),
                apply_settings_before_print: ko.observable(currentCamera.apply_settings_before_print()),
                address: ko.observable(currentCamera.address()),
                snapshot_request_template: ko.observable(currentCamera.snapshot_request_template()),
                ignore_ssl_error: ko.observable(currentCamera.ignore_ssl_error()),
                username: ko.observable(currentCamera.username()),
                password: ko.observable(currentCamera.password()),
                brightness: ko.observable(currentCamera.brightness()),
                brightness_request_template: ko.observable(currentCamera.brightness_request_template()),
                contrast: ko.observable(currentCamera.contrast()),
                contrast_request_template: ko.observable(currentCamera.contrast_request_template()),
                saturation: ko.observable(currentCamera.saturation()),
                saturation_request_template: ko.observable(currentCamera.saturation_request_template()),
                white_balance_auto: ko.observable(currentCamera.white_balance_auto()),
                white_balance_auto_request_template: ko.observable(currentCamera.white_balance_auto_request_template()),
                gain: ko.observable(currentCamera.gain()),
                gain_request_template: ko.observable(currentCamera.gain_request_template()),
                powerline_frequency: ko.observable(currentCamera.powerline_frequency()),
                powerline_frequency_request_template: ko.observable(currentCamera.powerline_frequency_request_template()),
                white_balance_temperature: ko.observable(currentCamera.white_balance_temperature()),
                white_balance_temperature_request_template: ko.observable(currentCamera.white_balance_temperature_request_template()),
                sharpness: ko.observable(currentCamera.sharpness()),
                sharpness_request_template: ko.observable(currentCamera.sharpness_request_template()),
                backlight_compensation_enabled: ko.observable(currentCamera.backlight_compensation_enabled()),
                backlight_compensation_enabled_request_template: ko.observable(currentCamera.backlight_compensation_enabled_request_template()),
                exposure_type: ko.observable(currentCamera.exposure_type()),
                exposure_type_request_template: ko.observable(currentCamera.exposure_type_request_template()),
                exposure: ko.observable(currentCamera.exposure()),
                exposure_request_template: ko.observable(currentCamera.exposure_request_template()),
                exposure_auto_priority_enabled: ko.observable(currentCamera.exposure_auto_priority_enabled()),
                exposure_auto_priority_enabled_request_template: ko.observable(currentCamera.exposure_auto_priority_enabled_request_template()),
                pan: ko.observable(currentCamera.pan()),
                pan_request_template: ko.observable(currentCamera.pan_request_template()),
                tilt: ko.observable(currentCamera.tilt()),
                tilt_request_template: ko.observable(currentCamera.tilt_request_template()),
                autofocus_enabled: ko.observable(currentCamera.autofocus_enabled()),
                autofocus_enabled_request_template: ko.observable(currentCamera.autofocus_enabled_request_template()),
                focus: ko.observable(currentCamera.focus()),
                focus_request_template: ko.observable(currentCamera.focus_request_template()),
                zoom: ko.observable(currentCamera.zoom()),
                zoom_request_template: ko.observable(currentCamera.zoom_request_template()),
                led1_mode: ko.observable(currentCamera.led1_mode()),
                led1_mode_request_template: ko.observable(currentCamera.led1_mode_request_template()),
                led1_frequency: ko.observable(currentCamera.led1_frequency()),
                led1_frequency_request_template: ko.observable(currentCamera.led1_frequency_request_template()),
                jpeg_quality: ko.observable(currentCamera.jpeg_quality()),
                jpeg_quality_request_template: ko.observable(currentCamera.jpeg_quality_request_template()),
            });
            self.settings.current_camera_guid(newGuid);
        };
        self.removeCamera = function (definition) {

            if (self.global_settings.settings.plugins.octolapse.cameras().length <= 1) {
                alert("You may not delete the last active camera");
                return;
            }

            self.global_settings.settings.plugins.octolapse.cameras.remove(definition);
            self.global_settings.settings.plugins.octolapse.current_camera_guid(
                self.global_settings.settings.plugins.octolapse.cameras()[0].guid);

        };
        self.resetCamera = function (definition) {
            var index = self.arrayFirstIndexOf(this.global_settings.settings.plugins.octolapse.cameras(),
                function (item) {
                    return item.guid() === definition.guid();
                });
            console.log(index);
            var currentCamera = this.global_settings.settings.plugins.octolapse.cameras()[index];
            var defaultCamera = this.global_settings.settings.plugins.octolapse.default_camera;
            //Set default values

            currentCamera.apply_settings_before_print(defaultCamera.apply_settings_before_print());
            currentCamera.address(defaultCamera.address());
            currentCamera.snapshot_request_template(defaultCamera.snapshot_request_template());
            currentCamera.ignore_ssl_error(defaultCamera.ignore_ssl_error());
            currentCamera.username(defaultCamera.username());
            currentCamera.password(defaultCamera.password());
            currentCamera.brightness(defaultCamera.brightness());
            currentCamera.brightness_request_template(defaultCamera.brightness_request_template());
            currentCamera.contrast(defaultCamera.contrast());
            currentCamera.contrast_request_template(defaultCamera.contrast_request_template());
            currentCamera.saturation(defaultCamera.saturation());
            currentCamera.saturation_request_template(defaultCamera.saturation_request_template());
            currentCamera.white_balance_auto(defaultCamera.white_balance_auto());
            currentCamera.white_balance_auto_request_template(defaultCamera.white_balance_auto_request_template());
            currentCamera.gain(defaultCamera.gain());
            currentCamera.gain_request_template(defaultCamera.gain_request_template());
            currentCamera.powerline_frequency(defaultCamera.powerline_frequency());
            currentCamera.powerline_frequency_request_template(defaultCamera.powerline_frequency_request_template());
            currentCamera.white_balance_temperature(defaultCamera.white_balance_temperature());
            currentCamera.white_balance_temperature_request_template(defaultCamera.white_balance_temperature_request_template());
            currentCamera.sharpness(defaultCamera.sharpness());
            currentCamera.sharpness_request_template(defaultCamera.sharpness_request_template());
            currentCamera.backlight_compensation_enabled(defaultCamera.backlight_compensation_enabled());
            currentCamera.backlight_compensation_enabled_request_template(defaultCamera.backlight_compensation_enabled_request_template());
            currentCamera.exposure_type(defaultCamera.exposure_type());
            currentCamera.exposure_type_request_template(defaultCamera.exposure_type_request_template());
            currentCamera.exposure(defaultCamera.exposure());
            currentCamera.exposure_request_template(defaultCamera.exposure_request_template());
            currentCamera.exposure_auto_priority_enabled(defaultCamera.exposure_auto_priority_enabled());
            currentCamera.exposure_auto_priority_enabled_request_template(defaultCamera.exposure_auto_priority_enabled_request_template());
            currentCamera.pan(defaultCamera.pan());
            currentCamera.pan_request_template(defaultCamera.pan_request_template());
            currentCamera.tilt(defaultCamera.tilt());
            currentCamera.tilt_request_template(defaultCamera.tilt_request_template());
            currentCamera.autofocus_enabled(defaultCamera.autofocus_enabled());
            currentCamera.autofocus_enabled_request_template(defaultCamera.autofocus_enabled_request_template());
            currentCamera.focus(defaultCamera.focus());
            currentCamera.focus_request_template(defaultCamera.focus_request_template());
            currentCamera.zoom(defaultCamera.zoom());
            currentCamera.zoom_request_template(defaultCamera.zoom_request_template());
            currentCamera.led1_mode(defaultCamera.led1_mode());
            currentCamera.led1_mode_request_template(defaultCamera.led1_mode_request_template());
            currentCamera.led1_frequency(defaultCamera.led1_frequency());
            currentCamera.led1_frequency_request_template(defaultCamera.led1_frequency_request_template());
            currentCamera.jpeg_quality(defaultCamera.jpeg_quality());
            currentCamera.jpeg_quality_request_template(defaultCamera.jpeg_quality_request_template());
        };
    };

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        OctolapseSettingsViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#octolapse_settings"]
    ]);
});


$(document).ready(function () {
    console.log("Octolapse Ready!");
});




