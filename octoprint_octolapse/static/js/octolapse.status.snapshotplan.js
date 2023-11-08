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
Octolapse.snapshotPlanStateViewModel = function() {
            var self = this;
            self.snapshot_plans = ko.observable([]);
            self.current_plan_index = ko.observable();
            self.plan_index = ko.observable();
            self.view_current_plan = ko.observable(true);
            self.current_file_line = ko.observable(0);

            self.plan_count = ko.observable(null);
            self.lines_remaining = ko.observable(null);
            self.lines_total = ko.observable(null);
            self.x_initial = ko.observable(null);
            self.y_initial = ko.observable(null);
            self.z_initial = ko.observable(null);
            self.x_return = ko.observable(null);
            self.y_return = ko.observable(null);
            self.z_return = ko.observable(null);

            self.format_coordinates = function(val)
            {
                if (val) return val.toFixed(2);
                return "";
            };

            self.multi_extruder = ko.observable(false);
            self.current_tool = ko.observable(0);
            self.progress_percent = ko.observable(null).extend({numeric: 2});
            self.snapshot_positions = ko.observableArray([]);
            self.is_animating_plans = ko.observable(false);
            self.travel_distance = ko.observable(0).extend({numeric: 1});
            self.saved_travel_distance = ko.observable(0).extend({numeric: 1});
            self.total_travel_distance = ko.observable(0).extend({numeric: 1});
            self.total_saved_travel_percent = ko.observable(0).extend({numeric: 1});
            self.printer_volume = null;
            self.axes = null;
            self.is_preview = false;
            self.is_confirmation_popup = ko.observable(false);
            self.autoclose = ko.observable(false);
            self.autoclose_seconds = ko.observable(0);
            self.quality_issues = ko.observableArray();
            self.missed_snapshots = ko.observable(0);

            setInterval(function() {
                var newTimer = self.autoclose_seconds() -1;
                self.autoclose_seconds(newTimer <= 0 ? 1 : newTimer);
            }, 1000);

            self.update = function (state) {
                if (state.snapshot_plans != null)
                {
                    self.snapshot_plans(state.snapshot_plans);
                    self.plan_count(state.snapshot_plans.length);
                    self.total_travel_distance(state.total_travel_distance);
                    var potential_total_distance = state.total_saved_travel_distance + state.total_travel_distance;
                    var percent_saved = 0;
                    if(potential_total_distance>0)
                    {
                        percent_saved = (state.total_saved_travel_distance / potential_total_distance) * 100.0;
                    }
                    self.total_saved_travel_percent(percent_saved);

                    if(typeof state.quality_issues !== 'undefined')
                    {
                        self.quality_issues(state.quality_issues);
                    }

                    if(typeof state.missed_snapshots !== 'undefined')
                    {
                        self.missed_snapshots(state.missed_snapshots);
                    }

                    if (typeof state.autoclose !== 'undefined') {
                        //console.log("Setting snapshot plan preview autoclose");
                        self.autoclose(state.autoclose);
                        self.autoclose_seconds(state.autoclose_seconds);
                    }
                    else {
                        console.error("Autoclose property not set!");
                    }
                }
                if (state.current_plan_index != null)
                {
                    self.current_plan_index(state.current_plan_index);
                    if (self.view_current_plan())
                    {
                        self.plan_index(state.current_plan_index);
                    }
                }
                if (state.current_file_line != null)
                    self.current_file_line(state.current_file_line);

                if (state.printer_volume != null)
                    self.printer_volume = state.printer_volume;

                if (state.axes != null)
                    self.axes = state.axes;

                self.update_current_plan();
            };

            self.update_current_plan = function()
            {
                if (! (self.snapshot_plans().length > 0 && self.plan_index() <  self.snapshot_plans().length))
                {
                    return;
                }

                var showing_plan = self.snapshot_plans()[self.plan_index()];
                var current_plan = self.snapshot_plans()[self.current_plan_index()];
                if (!(showing_plan && current_plan))
                    return;
                var previous_plan = null;
                var previous_line = 0;

                var lines_remaining = current_plan.file_gcode_number - self.current_file_line();

                self.lines_remaining(lines_remaining);
                var previous_line = 0;
                if (self.current_plan_index() - 1 > 0)
                    previous_plan = self.snapshot_plans()[self.current_plan_index() - 1];
                if (previous_plan != null)
                    previous_line = previous_plan.file_gcode_number;
                var lines_total = current_plan.file_gcode_number - previous_line;
                self.lines_total(lines_total);
                self.progress_percent((1-(lines_remaining / lines_total)) * 100);

                self.multi_extruder(showing_plan.initial_position.extruders.length > 1);
                self.current_tool(showing_plan.initial_position.current_tool);

                self.x_initial(showing_plan.initial_position.x);
                self.y_initial(showing_plan.initial_position.y);
                self.z_initial(showing_plan.initial_position.z);
                if (showing_plan.return_position) {
                    self.x_return(showing_plan.return_position.x);
                    self.y_return(showing_plan.return_position.y);
                    self.z_return(showing_plan.return_position.z);
                }
                else
                {
                    self.x_return(showing_plan.initial_position.x);
                    self.y_return(showing_plan.initial_position.y);
                    self.z_return(showing_plan.initial_position.z);
                }
                self.travel_distance(showing_plan.total_travel_distance);
                self.saved_travel_distance(showing_plan.total_saved_travel_distance);
                var x_current = showing_plan.initial_position.x;
                var y_current = showing_plan.initial_position.y;
                var z_current = showing_plan.initial_position.z;
                var snapshot_positions = [];
                // Create snapshot positions from steps
                for (var stepIndex = 0; stepIndex < showing_plan.steps.length; stepIndex++)
                {
                    var current_step = showing_plan.steps[stepIndex];
                    if (current_step.action == "travel")
                    {
                        if (current_step.x != null)
                            x_current = current_step.x;
                        if (current_step.y != null)
                            y_current = current_step.y;
                        if (current_step.z != null)
                            z_current = current_step.z;
                    }
                    else if(current_step.action == "snapshot")
                    {
                        snapshot_positions.push({x: x_current, y: y_current, z: z_current});
                    }
                }
                self.snapshot_positions(snapshot_positions);
                // Update Canvass
                self.updateCanvas();
            };

            self.next_plan_clicked = function()
            {
                self.is_animating_plans(false);
                self.view_current_plan(false);
                if (self.snapshot_plans().length < 1)
                    return;

                var index = self.plan_index()+1;
                if (index < self.snapshot_plans().length)
                {
                    self.plan_index(index);
                }
                else
                {
                    self.plan_index(0);
                }
                self.update_current_plan();
                return false;
            };

            self.previous_plan_clicked = function()
            {
                self.is_animating_plans(false);
                self.view_current_plan(false);
                if (self.snapshot_plans().length < 1)
                    return false;
                var index = self.plan_index()-1;
                if (index > -1)
                {
                    self.plan_index(index);
                }
                else
                {
                    self.plan_index(self.snapshot_plans().length - 1);
                }
                self.update_current_plan();
                return false;
            };

            self.show_current_plan_clicked = function()
            {
                self.is_animating_plans(false);
                self.view_current_plan(true);
                self.plan_index(self.current_plan_index());
                self.update_current_plan();
                return false;
            };

            self.animate_plan_clicked = function()
            {
                if(self.is_animating_plans()) {
                    //console.log("Octolapse - Snapshot Plans are already animating.");
                    return;
                }
                //console.log("Animating Snapshot Plans.");
                self.is_animating_plans(true);
                self.view_current_plan(false);

                if (self.snapshot_plans().length>0)
                    self.animate_plan(0);
            };

            self.animate_plan = function(index)
            {
                setTimeout(function() {
                    if (!self.is_animating_plans())
                        return;
                    self.plan_index(index);
                    self.update_current_plan();
                    index++;
                    if (index < self.snapshot_plans().length)
                        self.animate_plan(index);
                    else
                    {
                        self.view_current_plan(true);
                        self.plan_index(self.current_plan_index());
                        self.is_animating_plans(false);
                        self.update_current_plan();
                    }
                }, 33.3);
            };
            // Canvass Variables
            self.canvas_printer_size = [125,125,125];
            self.canvas_border_size = [14,14,14];
            self.legend_size = [115,0,0];
            self.canvas_size = [
                self.canvas_printer_size[0]+self.canvas_border_size[0]*2+self.legend_size[0],
                self.canvas_printer_size[1]+self.canvas_border_size[1]*2+self.legend_size[1],
                self.canvas_printer_size[2]+self.canvas_border_size[2]*2+self.legend_size[2]
            ];

            self.printer_volume = null;
            self.x_canvas_scale = null;
            self.y_canvas_scale = null;
            self.z_canvas_scale = null;

            self.initial_position_radius=5;
            self.snapshot_position_radius=4;
            self.canvas_location_radius=3;
            self.preview_canvas = null;
            self.info_panel_canvas = null;
            self.canvas = null;
            self.canvas_context = null;
            self.preview_canvas_context = null;
            self.info_panel_canvas_context = null;
            self.line_width = 2;
            self.updateCanvas = function () {
                self.canvas_update_scale();
                self.get_canvas();
                if (self.canvas === null)
                {
                    if (self.is_preview) {
                        self.canvas_selector = "#octolapse_snapshot_plan_preview_dialog #snapshot_plan_canvas_container";
                    }
                    else
                    {
                        self.canvas_selector = "#snapshot_plan_info_panel #snapshot_plan_canvas_container";
                    }
                    self.canvas = document.createElement('canvas');
                    if(self.is_preview)
                        self.preview_canvas = self.canvas;
                    else
                        self.info_panel_canvas = self.canvas;
                    self.canvas.width = self.canvas_size[0];
                    self.canvas.height = self.canvas_size[1];
                    $(self.canvas).attr('id','snapshot_plan_canvas').text('unsupported browser')
                        .appendTo(self.canvas_selector);
                    self.canvas_context = self.canvas.getContext('2d');
                    self.canvas.lineWidth = self.line_width;
                    self.canvas_erase_contents();
                    self.canvas_draw_axis();
                    self.canvas_draw_legend();
                    self.save_canvas();
                }
                if (self.canvas_context == null)
                {
                    console.error("Octolapse - Unable to create canvas context!");
                    return;
                }
                self.canvas_erase_print_bed_and_axis();
                self.canvas_draw_axis();
                self.canvas_draw_print_bed();
                self.canvas_draw_start_location();
                self.canvas_draw_snapshot_locations();
                self.canvas_draw_return_location();

            };
            self.get_canvas = function()
            {
                if (self.is_preview) {
                    self.canvas_selector = "#octolapse_snapshot_plan_preview_dialog #snapshot_plan_canvas_container";
                    self.canvas = self.preview_canvas;
                    self.canvas_context = self.preview_canvas_context;
                }
                else
                {
                    self.canvas_selector = "#snapshot_plan_info_panel #snapshot_plan_canvas_container";
                    self.canvas = self.info_panel_canvas;
                    self.canvas_context = self.info_panel_canvas_context;
                }
            };

            self.save_canvas = function()
            {
                if (self.is_preview) {
                    self.preview_canvas = self.canvas;
                    self.preview_canvas_context = self.canvas_context;
                }
                else
                {
                    self.info_panel_canvas = self.canvas;
                    self.info_panel_canvas_context = self.canvas_context;
                }
            };


            self.canvas_update_scale = function()
            {
                self.x_canvas_scale = self.canvas_printer_size[0]/(self.printer_volume.max_x - self.printer_volume.min_x);
                self.y_canvas_scale = self.canvas_printer_size[1]/(self.printer_volume.max_y - self.printer_volume.min_y);
                self.z_canvas_scale = self.canvas_printer_size[2]/(self.printer_volume.max_z - self.printer_volume.min_z);
            };

            self.canvas_draw_print_bed = function()
            {
                if (self.printer_volume.bed_type == 'circular'){
                    self.canvas_draw_circular_bed();
                }
                else {
                    self.canvas_draw_rectangular_bed();
                }

            };

            self.canvas_draw_circular_bed = function() {
                // draw a circle around the print area
                // draw the x axis linebottom border plus the intersection
                self.canvas_context.strokeStyle = '#000000';
                // get the center coordinates and radius
                var radius = self.canvas_printer_size[0]/2;
                var center_x = self.canvas_border_size[0] + self.canvas_printer_size[0]/2;
                var center_y = self.canvas_border_size[1] + self.canvas_printer_size[1]/2;

                // draw the outside
                self.canvas_context.beginPath();
                self.canvas_context.arc(center_x,center_y, radius, 0, 2 * Math.PI);
                self.canvas_context.stroke();

                //draw inner rings
                var num_increments = 4;
                var radius_increment = radius/num_increments;
                for (var increment = 0; increment<num_increments ; increment++)
                {
                    // draw the inner ring
                    radius = radius - radius_increment;
                    self.canvas_context.beginPath();
                    self.canvas_context.arc(center_x,center_y, radius, 0, 2 * Math.PI);
                    self.canvas_context.stroke();
                }
            };

            self.canvas_draw_rectangular_bed = function() {
                // draw a line around the print area
                // draw the x axis linebottom border plus the intersection
                self.canvas_context.strokeStyle = '#000000';
                // draw the outside
                self.canvas_context.beginPath();
                self.canvas_context.rect(
                    self.canvas_border_size[0],
                    self.canvas_border_size[1],
                    self.canvas_printer_size[0],
                    self.canvas_printer_size[1]
                );
                self.canvas_context.stroke();
                //draw grid lines
                var num_increments = 4;
                for (var increment = 0; increment<num_increments ; increment++)
                {
                    var x = self.canvas_printer_size[0]/num_increments*increment;
                    var y = self.canvas_printer_size[1]/num_increments*increment;
                    // draw the vertical separator.
                    self.canvas_context.beginPath();
                    self.canvas_context.moveTo(self.canvas_border_size[0]+x, self.canvas_border_size[1]);
                    self.canvas_context.lineTo(self.canvas_border_size[0]+x, self.canvas_border_size[1] + self.canvas_printer_size[1]);
                    self.canvas_context.stroke();
                    // draw the horizontal separator
                    self.canvas_context.beginPath();
                    self.canvas_context.moveTo(self.canvas_border_size[0], self.canvas_border_size[1]+y);
                    self.canvas_context.lineTo(self.canvas_border_size[0]+self.canvas_printer_size[0], self.canvas_border_size[1]+y);
                    self.canvas_context.stroke();
                }
            };

            self.axis_line_length = 25;

            self.canvas_draw_axis = function() {
                self.canvas_context.strokeStyle = '#000000';
                // **draw the x arrow
                // draw the vertical line
                self.canvas_context.beginPath();
                self.canvas_context.moveTo(
                    self.canvas_border_size[0] * 0.5,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5
                );
                self.canvas_context.lineTo(
                    self.canvas_border_size[0] * 0.5,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5 - self.axis_line_length
                );
                self.canvas_context.stroke();
                // draw the left side of the arrow
                self.canvas_context.beginPath();
                self.canvas_context.moveTo(
                    self.canvas_border_size[0] * 0.5,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5 - self.axis_line_length
                );
                self.canvas_context.lineTo(
                    self.canvas_border_size[0] * 0.25,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.75 - self.axis_line_length
                );
                self.canvas_context.stroke();
                // draw the right side of the arrow
                self.canvas_context.beginPath();
                self.canvas_context.moveTo(
                    self.canvas_border_size[0] * 0.5,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5 - self.axis_line_length
                );
                self.canvas_context.lineTo(
                    self.canvas_border_size[0] * 0.75,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.75 - self.axis_line_length
                );
                self.canvas_context.stroke();
                // draw the Y label
                self.canvas_context.fillStyle = "#000000";
                self.canvas_context.textAlign="left";
                var text_width = self.canvas_context.measureText("Y");
                self.canvas_context.font = "12px Helvetica Neue,Helvetica,Arial,sans-serif";
                self.canvas_context.fillText(
                    "Y",
                    self.canvas_border_size[0] * 0.5 - text_width.width/2 - 1,
                    self.canvas_printer_size[1] - self.axis_line_length + self.canvas_border_size[1] * 1.5 - 2
                );

                // *** draw the X arrow
                // draw the horizontal line
                self.canvas_context.beginPath();
                self.canvas_context.moveTo(
                    self.canvas_border_size[0] * 0.5,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5
                );
                self.canvas_context.lineTo(
                    self.canvas_border_size[0] * 0.5 + self.axis_line_length,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5
                );
                self.canvas_context.stroke();
                // draw the top side of the arrow
                self.canvas_context.beginPath();
                self.canvas_context.moveTo(
                    self.canvas_border_size[0] * 0.5 + self.axis_line_length,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5
                );
                self.canvas_context.lineTo(
                    self.canvas_border_size[0] * 0.25 + self.axis_line_length,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.25
                );
                self.canvas_context.stroke();
                // draw the right side of the arrow
                self.canvas_context.beginPath();
                self.canvas_context.moveTo(
                    self.canvas_border_size[0] * 0.5 + self.axis_line_length,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5
                );
                self.canvas_context.lineTo(
                    self.canvas_border_size[0] * 0.25 + self.axis_line_length,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.75
                );
                self.canvas_context.stroke();
                // draw the X label
                self.canvas_context.fillStyle = "#000000";
                self.canvas_context.textAlign="left";
                self.canvas_context.font = "12px Helvetica Neue,Helvetica,Arial,sans-serif";
                self.canvas_context.fillText(
                    "X",
                    self.canvas_border_size[0] * 0.5 + self.axis_line_length,
                    self.canvas_printer_size[1] + self.canvas_border_size[1] * 1.5 + 4.5
                );

            };

            self.canvas_draw_legend = function() {

                var lineHeight = 18;
                x = self.canvas_border_size[0]*2+self.canvas_printer_size[0];
                y = self.canvas_border_size[1]*2;

                // *** Initial Position
                // Draw the start circul
                self.canvas_context.strokeStyle = '#ff0000';
                self.canvas_context.beginPath();
                self.canvas_context.arc(x,y, self.initial_position_radius, 0, 2 * Math.PI);
                self.canvas_context.stroke();// draw start circle
                // Draw the start  position text
                self.canvas_context.fillStyle = "#000000";
                self.canvas_context.textAlign="left";
                var text = "Start";
                self.canvas_context.font = "12px Helvetica Neue,Helvetica,Arial,sans-serif";
                self.canvas_context.fillText(
                    text,
                    x + self.initial_position_radius*2,
                    y + self.initial_position_radius
                );
                // Snapshot Position
                // draw the circle
                y+= lineHeight;
                self.canvas_context.strokeStyle = '#0000ff';
                self.canvas_context.beginPath();
                self.canvas_context.arc(x,y, self.snapshot_position_radius, 0, 2 * Math.PI);
                self.canvas_context.stroke();// draw start circle
                // Draw the start  position text
                self.canvas_context.fillStyle = "#000000";
                self.canvas_context.textAlign="left";
                text = "Snapshot";
                self.canvas_context.font = "12px Helvetica Neue,Helvetica,Arial,sans-serif";
                self.canvas_context.fillText(
                    text,
                    x + self.initial_position_radius*2,
                    y + self.snapshot_position_radius
                );
                // Return Position
                // draw the circle
                y += lineHeight;
                self.canvas_context.fillStyle = '#00ff00';
                self.canvas_context.beginPath();
                self.canvas_context.arc(x,y, self.canvas_location_radius, 0, 2 * Math.PI);
                self.canvas_context.fill();// draw start circle
                // Draw the start  position text
                self.canvas_context.fillStyle = "#000000";
                self.canvas_context.textAlign="left";
                text = "Return";
                self.canvas_context.font = "12px Helvetica Neue,Helvetica,Arial,sans-serif";
                self.canvas_context.fillText(
                    text,
                    x + self.initial_position_radius*2,
                    y + self.canvas_location_radius
                );
            };

            self.canvas_erase_contents = function(){
                self.canvas_context.fillStyle = '#ffffff';
                self.canvas_context.fillRect(0,0,self.canvas_size[0],self.canvas_size[1]);
            };

            self.canvas_erase_print_bed_and_axis = function(){
                //console.log("Erasing Bed");
                self.canvas_context.fillStyle = '#ffffff';
                self.canvas_context.fillRect(
                    0,
                    0,
                    self.canvas_border_size[0] + self.initial_position_radius + self.canvas_printer_size[0] + self.line_width,
                    self.canvas_border_size[1] + self.initial_position_radius + self.canvas_printer_size[1]  + self.line_width
                    //self.canvas_printer_size[0] + self.canvas_location_radius*2,
                    //self.canvas_printer_size[1] + self.canvas_location_radius*2
                );
            };

            self.canvas_draw_start_location = function() {
                self.canvas_context.strokeStyle = '#ff0000';
                self.canvas_context.beginPath();
                self.canvas_context.arc(self.to_canvas_x(self.x_initial()), self.to_canvas_y(self.y_initial()), self.initial_position_radius, 0, 2 * Math.PI);
                self.canvas_context.stroke();
            };

            self.canvas_draw_snapshot_locations = function() {
                self.canvas_context.strokeStyle = '#0000ff';
                if (self.snapshot_positions() == null)
                    return;
                for (var index = 0; index < self.snapshot_positions().length; index++)
                {
                    var position = self.snapshot_positions()[index];
                    self.canvas_context.beginPath();
                    self.canvas_context.arc(self.to_canvas_x(position.x), self.to_canvas_y(position.y), self.snapshot_position_radius, 0, 2 * Math.PI);
                    self.canvas_context.stroke();
                }
            };

            self.canvas_draw_return_location = function()
            {
                if(self.x_return() == null || self.y_return == null)
                    return;
                self.canvas_context.fillStyle = '#00ff00';
                self.canvas_context.beginPath();
                self.canvas_context.arc(self.to_canvas_x(self.x_return()), self.to_canvas_y(self.y_return()), self.canvas_location_radius, 0, 2 * Math.PI);
                self.canvas_context.fill();
            };

            self.invert_coordinate = function(coord, min, max){
                return (max - min) - coord;
            };

            self.normalize_coordinate = function(coord, min, max)
            {
                if (self.printer_volume.origin_type == 'center')
                {
                    return coord + (max - min) / 2.0;
                }
                else
                {
                    return coord - min;
                }

            };

            self.to_canvas_x = function(x)
            {
                x = self.normalize_coordinate(x, self.printer_volume.min_x, self.printer_volume.max_x);
                return x *self.x_canvas_scale + self.canvas_border_size[0];
            };

            self.to_canvas_y = function(y)
            {
                y = self.normalize_coordinate(y, self.printer_volume.min_y, self.printer_volume.max_y);
                // Y coordinates are flipped on the camera when compared to the standard 3d printer
                // coordinates, so invert the coordinate
                y = self.invert_coordinate(y, self.printer_volume.min_y, self.printer_volume.max_y);

                return y*self.y_canvas_scale + self.canvas_border_size[1];
            };

            self.to_canvas_z = function(z)
            {
                // This isn't right, z coordinates always start at 0!
                z = self.normalize_coordinate(z, 0, 0);
                return z *self.z_canvas_scale + self.canvas_border_size[2];
            };

        };
