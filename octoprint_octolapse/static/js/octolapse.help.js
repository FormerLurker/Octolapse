$(function () {
    OctolapseHelp = function () {
        var self = this;
        self.popup_margin = 15;
        self.popup_width_with_margin = 900;
        self.popup_width = self.popup_width_with_margin - self.popup_margin*2;

        self.stack_center = {
            "dir1": "down",
            "dir2": "right",
            "firstpos1": self.popup_margin,
            "firstpos2": (document.body.clientWidth / 2) - (self.popup_width / 2 + self.popup_margin),
            "modal": true
        };

        self.options = {
            title: "Octolapse Help",
            text: "unknown",
            hide: false,
            stack: self.stack_center,
            width: self.popup_width.toString() + "px",
            addclass: 'octolapse-pnotify-help',
            type: "info",
            icon: 'fa fa-question-circle fa-lg',
            Buttons: {
              closer: false,
              sticker: false

            },
            confirm: {
                confirm: true,
                buttons: [{
                    text: 'Close',
                    primary: true,
                    click: function(notice) {
                      notice.remove();
                    }},{
                        text: 'Close',
                        addClass: 'remove_button'
                    }
                ]
            },
            before_open: function(notice) {
                // We want to remove the default button, else two will show
                var notice = notice.get();
                notice.find(".remove_button").remove();
                // Now we want to put the notice inside another div so we can add an overlay effect
                // since modal doesn't seem to be working in this version of pnotify (I could be wrong
                // but the docs I can find are definitely not for this version.)
            },
            after_open: function(notice) {
                // first create a div and insert it before the notice
                var $container = $('<div class="octolapse-pnotify-container"></div>').insertBefore(notice.elem);
                var $overlay = $('<div class="octolapse-pnotify-overlay modal-backdrop fade in" style="z-index:1070"></div>');
                // now move our notice inside of the new div
                $(notice.elem).appendTo($container);
                $overlay.appendTo($container);
                $overlay.click(function(){
                    notice.remove();
                });
                console.log("Adding resize handler.");
                $(window).on("resize",self.resize_handler);
            },
            after_close: function(notice){
                var $parentDiv = $(notice.elem).parent();
                $parentDiv.remove();
                console.log("Removing resize handler.");
                $(window).off("resize", self.resize_handler);
            }
        };

        self.resize_handler = function(event) {
            console.log("Resizing octolapse help.");
            var width = self.popup_width.toString() + "px";
            if (document.body.clientWidth < self.popup_width_with_margin) {
                self.stack_center.firstpos2 = self.popup_margin;
                width = (document.body.clientWidth - (self.popup_margin * 2)).toString() + "px";
            }
            else {
                self.stack_center.firstpos2 = (document.body.clientWidth / 2) - (self.popup_width / 2);
            }
            $(".octolapse-pnotify-help").css("width", width);
        };

        self.converter = new showdown.Converter({
            'openLinksInNewWindow': true,
            'simpleLineBreaks': true
        });

        self.converter.setFlavor('github');

        self.showHelpForLink = function (doc, title)
        {
            url = "/plugin/octolapse/static/docs/help/" + doc + "?nonce=" + Date.now().toString();
            $.ajax({
                url: url,
                type: "GET",
                dataType: "text",
                success: function (results) {
                    var body_color = $("body").css('color');
                    var body_background_color = $("body").css('background-color');
                    var body_font_weight = $("body").css('font-weight');
                    //console.log(results);
                    self.options.text = Octolapse.replaceAll(self.converter.makeHtml(results), '\n','');
                    self.options.title = title;

                    Octolapse.displayPopupForKey(self.options, "help", ["help"]);
                    $(".octolapse-pnotify-help div.ui-pnotify-container")
                        .css("background-color", body_background_color)
                        .css("border-color", "#000000")
                        .css("border-width", "3px")
                        .css("color", body_color)
                        .css("font-weight", body_font_weight);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    if (errorThrown === "NOT FOUND")
                    {
                        var body_color = $("body").css('color');
                        var body_background_color = $("body").css('background-color');
                        var body_font_weight = $("body").css('font-weight');
                        var missing_file_text = "The requested help file could not be found.  Please report this error\
                            [here](https://github.com/FormerLurker/Octolapse/issues) and visit the\
                            [wiki](https://github.com/FormerLurker/Octolapse/wiki) to find help for this item.";
                        self.options.text = self.converter.makeHtml(missing_file_text);
                        self.options.title = "Help Could Not Be Found";

                        Octolapse.displayPopupForKey(self.options, "help", ["help"]);
                        $(".octolapse-pnotify-help div.ui-pnotify-container")
                            .css("background-color", body_background_color)
                            .css("border-color", "#000000")
                            .css("border-width", "3px")
                            .css("color", body_color)
                            .css("font-weight", body_font_weight);
                    }
                    else {
                        var options = {
                            title: 'Error',
                            text: "Unable to retrieve help for '" + title + "'!  Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "help", ["help"]);
                    }
                }
            });
        };

        self.bindHelpLinks = function(selector)
        {
            var default_selector = ".octolapse_help[data-help-url]";
            selector = selector + " " + default_selector;

            console.log("octolapse.help.js - Binding help links to " + selector);
            $(selector).each(function(){
               if (!$(this).attr('title'))
                   $(this).attr('title',"Click for help with this");
               if($(this).children().length == 0) {
                   var icon = $('<span class="fa fa-question-circle fa-lg"></span>');
                   $(this).append(icon);
               }
            });
            $(selector).unbind("click");
            $(selector).click( function(e) {
                console.log("octolapse.help.js - Help link clicked");
               // get the data group data
                var url = $(this).data('help-url');
                var title = $(this).data('help-title');
                if (!title)
                    title = "Help";
                self.showHelpForLink(url,title);
                e.preventDefault();
            });
        };
    }
});
