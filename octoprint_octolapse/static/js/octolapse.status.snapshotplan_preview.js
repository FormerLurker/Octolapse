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
    Octolapse.SnapshotPlanPreviewPopupViewModel = function (values) {
        var self = this;
        self.on_closed_callback = values.on_closed;

        self.openDialog = function()
        {
            var dialog = this;
            dialog.$snapshotPlanPreviewDialog = $("#octolapse_snapshot_plan_preview_dialog");
            dialog.$snapshotPlanPreviewForm = dialog.$snapshotPlanPreviewDialog.find("#octolapse_snapshot_plan_preview_form");
            dialog.$cancelButton = $(".cancel", dialog.$snapshotPlanPreviewDialog);
            dialog.$closeIcon = $("a.close", dialog.$snapshotPlanPreviewDialog);
            dialog.$continueButton = $(".continue", dialog.$snapshotPlanPreviewDialog);
            dialog.$modalBody = dialog.$snapshotPlanPreviewDialog.find(".modal-body");
            dialog.$modalHeader = dialog.$snapshotPlanPreviewDialog.find(".modal-header");
            dialog.$modalFooter = dialog.$snapshotPlanPreviewDialog.find(".modal-footer");
            dialog.$cancelButton.unbind("click");
            // Called when the user clicks the cancel button in any add/update dialog
            dialog.$cancelButton.bind("click", self.rejectSnapshotPlan);
            dialog.$closeIcon.bind("click", self.rejectSnapshotPlan);

            dialog.$continueButton.unbind("click");
            // Called when the user clicks the cancel button in any add/update dialog
            dialog.$continueButton.bind("click", function () {
                // Save the settings.
                Octolapse.Globals.acceptSnapshotPlanPreview();
                self.closeSnapshotPlanPreviewDialog();
            });

            // Prevent hiding unless the event was initiated by the hideAddEditDialog function
            dialog.$snapshotPlanPreviewDialog.on("hide.bs.modal", function () {
                return self.can_hide;
            });

            dialog.$snapshotPlanPreviewDialog.on("hidden.bs.modal", function () {
            });

            dialog.$snapshotPlanPreviewDialog.on("show.bs.modal", function () {
                Octolapse.Status.SnapshotPlanState.is_confirmation_popup(true);
            });

            dialog.$snapshotPlanPreviewDialog.on("shown.bs.modal", function () {
                Octolapse.Help.bindHelpLinks("#octolapse_snapshot_plan_preview_dialog");

                dialog.$snapshotPlanPreviewDialog.css({
                    width: '940px',
                    'margin-left': function () {
                        return -($(this).width() / 2);
                    }
                });

            });
            dialog.$snapshotPlanPreviewDialog.modal({
                backdrop: 'static',
                maxHeight: function() {
                    return Math.max(
                      window.innerHeight - dialog.$modalHeader.outerHeight()-dialog.$modalFooter.outerHeight()-66,
                      200
                    );
                }
            });
        };

        self.rejectSnapshotPlan = function(){
            // reject the plan and close the popup.
            Octolapse.Globals.cancelPreprocessing();
            self.closeSnapshotPlanPreviewDialog();
        };

        // hide the modal dialog
        self.can_hide = false;
        self.closeSnapshotPlanPreviewDialog = function() {
            self.can_hide = true;
            $("#octolapse_snapshot_plan_preview_dialog").modal("hide");
            Octolapse.Status.SnapshotPlanState.is_confirmation_popup(false);
            if(self.on_closed_callback)
                self.on_closed_callback();
        };

        self.cancelPreview = function(){
            Octolapse.Globals.cancelPreprocessing();
        };

        self.acceptPreview = function() {
            Octolapse.Globals.acceptSnapshotPlanPreview();
        };

    };
});
