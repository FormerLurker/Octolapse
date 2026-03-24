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
$(function () {
    Octolapse.ListViewColumn = function(text, id, options){
        var self = this;
        self.text = text;
        self.id = id;
        self.sortable = (options || {}).sortable || false;
        self.sort_column_id = (options || {}).sort_column_id || id;
        self.classes = (options || {}).class || "";
        self.template_id = (options || {}).template_id || "octolapse-list-item";
        self.visible_observable = (options || {}).visible_observable || true;
    };

    Octolapse.ListItemViewModel = function(parent, id, name, title, selected, value){
        var self = this;
        self.id = id;
        self.name = name;
        self.title = title;
        self.value = value;
        self.data = ko.observable();
        self.data.parent = parent;
        //self.selected = ko.observable(!!selected);
        self.selected = ko.observable(!!selected);
        self.disabled = ko.observable(false);
        self.get_list_item_value = function(column){
            var value = null;
            if (self.value !== null && self.value[column.id] !== undefined)
                value = self.value[column.id];
            else if (self[column.id] !== undefined)
                value = self[column.id];

            return {
                item: self,
                column: column,
                value: value
            };
        };
    };

    Octolapse.ListViewModel = function (parent, id, options){
        var self = this;
        self.data = ko.observable();
        self.data.parent = parent;
        self.list_id = id;
        self.options = options ? options : {};
        self.current_page_index = ko.observable(0);
        self.all_selected = ko.observable(false);
        self.page_selected = ko.observable(false);
        self.page_size = ko.observable(10);
        self.has_loaded = ko.observable(false);
        // Must be at least 6 pages, can be more.
        self.list_items = ko.observableArray([]);
        self.page_sizes = [
            {name: "10", value: 10},
            {name: "25", value: 25},
            {name: "50", value: 50},
            {name: "100", value: 100},
            {name: "250", value: 250},
            {name: "500", value: 500}
        ];
        self.pager_values = ko.observableArray([]);
        self.selection_enabled = false;
        if (self.options.selection_enabled !== undefined)
        {
            self.selection_enabled = self.options.selection_enabled;
        }

        self.select_all_enabled = false;
        if (self.options.select_all_enabled !== undefined)
        {
            self.select_all_enabled = self.options.select_all_enabled;
        }
        self.action_text = self.options.action_text || "Action";
        self.on_resize = self.options.on_resize;
        self.columns = self.options.columns || [new Octolapse.ListViewColumn('Name', 'name')];
        self.action_class = self.options.action_class || 'list-item-action';
        self.selection_class = self.options.selection_class || 'list-item-selection';
        self.selection_header_class = self.options.selection_header_class || 'list-item-selection';
        self.to_list_item = self.options.to_list_item || function(item) {
            return new Octolapse.ListItemViewModel(self.data.parent, item.name, item.name, item.name, false, null);
        };
        self.no_items_template_id = self.options.no_items_template_id || "octolapse-list-no-items";
        self.header_template_id = self.options.header_template_id || "octolapse-list-item-header";
        self.list_item_template_id = self.options.list_item_template_id || "octolapse-list-item";
        self.top_left_pagination_template_id = self.options.top_left_pagination_template_id || "octolapse-list-empty-template";
        self.top_right_pagination_template_id = self.options.top_right_pagination_template_id || "octolapse-list-empty-template";
        self.bottom_left_pagination_template_id = self.options.bottom_left_pagination_template_id || "octolapse-list-empty-template";
        self.bottom_right_pagination_template_id = self.options.bottom_right_pagination_template_id || "octolapse-pagination-page-size";
        self.select_header_template_id = self.options.select_header_template_id || "octolapse-list-select-header-checkbox-page-template";
        self.custom_row_template_id = self.options.custom_row_template_id || null;
        self.sort_column = ko.observable(self.options.sort_column || "name");
        self.sort_direction_ascending = ko.observable((self.options.sort_direction || "ascending") === "ascending");
        self.default_sort_direction_ascending = self.sort_direction_ascending();
        self.not_loaded_template_id = options.not_loaded_template_id || "octolapse-list-not-loaded";
        self.pagination_pages = self.options.pagination_pages || 11;
        self.pagination_style = self.options.pagination_style || "normal";
        self.pagination = self.options.pagination || "top-and-bottom";
        self.pagination_top = self.pagination === 'top' || self.pagination === "top-and-bottom";
        self.pagination_bottom = self.pagination === 'bottom' || self.pagination === "top-and-bottom";
        self.pagination_row_auto_hide = self.options.pagination_row_auto_hide === undefined? true : self.options.pagination_row_auto_hide;

        self.pagination_top_left_class = "span2";
        self.pagination_top_center_class = "span8";
        self.pagination_top_right_class = "span2";
        self.pagination_bottom_left_class = "span2";
        self.pagination_bottom_center_class = "span8";
        self.pagination_bottom_right_class = "span2";

        if (self.pagination_style === 'wide')
        {
            self.pagination_top_left_class = "span1";
            self.pagination_top_center_class = "span10";
            self.pagination_top_right_class = "span1";
            self.pagination_bottom_left_class = "span1";
            self.pagination_bottom_center_class = "span10";
            self.pagination_bottom_right_class = "span1";
            if (!self.options.pagination_pages)
                self.pagination_pages = 13;
        }
        else if (self.pagination_style === "narrow")
        {
            self.pagination_top_left_class = "span3";
            self.pagination_top_center_class = "span6";
            self.pagination_top_right_class = "span3";
            self.pagination_bottom_left_class = "span3";
            self.pagination_bottom_center_class = "span6";
            self.pagination_bottom_right_class = "span3";
            if (!self.options.pagination_pages)
                self.pagination_pages = 9;
        }

        self.show_pagination_row_top = ko.pureComputed(function(){
            return self.pagination_top && (self.list_items().length > 0 || !self.pagination_row_auto_hide);
        });

        self.show_pagination_row_bottom = ko.pureComputed(function(){
            return self.pagination_bottom && (self.list_items().length > 0 || !self.pagination_row_auto_hide);
        });

        self.resize = function(){
            //console.log("octolapse.helpers.js - resize");
            if (self.on_resize)
                self.on_resize();
        };
        self.is_empty = ko.pureComputed(function(){
            return self.list_items().length == 0;
        });

        self.all_selected.subscribe(function(value){
            //console.log("octolapse.helpers.js - all selected");
            self.select('all', value);
        });

        self.page_selected.subscribe(function(value){
            //console.log("octolapse.helpers.js - page selected");
            self.select('page', value);
        });

        self.page_size.octolapseSubscribeChanged(function (newValue, oldValue) {
            //console.log("octolapse.helpers.js - page size changed");
            var new_page = Math.floor(self.current_page_index()*oldValue/newValue);
            self.current_page_index(new_page);
            self.resize();
        });

        self.num_pages = ko.pureComputed(function(){
            //console.log("octolapse.helpers.js - num pages changed");
            if (self.list_items().length === 0)
                return 0;
            return Math.ceil(self.list_items().length / self.page_size());
        });

        self.pager = ko.pureComputed(function(){
            //console.log("octolapse.helpers.js - pager changed");
            if (self.pagination_pages < 6) {
                console.error("The file browser pager must have at least 6 pages.");
                return [];
            }
            // determine how many pager items will be in the array.  Can be 0-self.num_pager_pages
            var num_pages = self.num_pages();
            if (num_pages < 1)
                return [];
            var pager_size = Math.min(self.pagination_pages, num_pages);
            var midpoint = Math.floor((self.pagination_pages - 4)/2);
            // If we have only one page, there is no need for a pager!

            var pager_pages = new Array(pager_size);
            // set the first and last page
            pager_pages[0] = new Octolapse.PagerPageViewModel('link', 0);
            pager_pages[pager_size-1] = new Octolapse.PagerPageViewModel('link', num_pages-1);
            for (var index=1; index < pager_size-1; index++)
            {
                // There are four scenarios to handle:
                if (num_pages <= self.pagination_pages)
                {
                    // 1. There are up to pagination_pages pages.  In that case just add the available indexes.
                    pager_pages[index] = new Octolapse.PagerPageViewModel('link', index);
                }
                else if (self.current_page_index() < self.pagination_pages - 3)
                {
                    // 2. We are in the first pagination_pages - 2 page.  In that case we want only one
                    //    ellipsis right before the final page.
                    if (index < self.pagination_pages - 2)
                    {
                        pager_pages[index] = new Octolapse.PagerPageViewModel('link', index);
                    }
                    else
                    {
                        pager_pages[index] = new Octolapse.PagerPageViewModel('ellipsis');
                    }
                }
                else if (self.current_page_index() < num_pages - self.pagination_pages + 3)
                {
                    // 3. We are in the last num_pages - (pagination_pages - 2) page.  In that case we want only one
                    //    ellipsis right after the first page.
                    if (index === 1 || index === self.pagination_pages - 2)
                    {
                        pager_pages[index] = new Octolapse.PagerPageViewModel('ellipsis');
                    }
                    else
                    {
                        pager_pages[index] = new Octolapse.PagerPageViewModel('link', self.current_page_index() - midpoint + index - 2 );
                    }
                }
                else
                {
                    // 4. We are at the end of the list.  In this case we want ellipsis after page 1 and before max_page
                    //    ellipsis right after the first page.
                    if (index === 1)
                    {
                        pager_pages[index] = new Octolapse.PagerPageViewModel('ellipsis');
                    }
                    else
                    {

                        pager_pages[index] = new Octolapse.PagerPageViewModel('link', num_pages - (self.pagination_pages - index));
                    }
                }
            }
            return pager_pages;
        });

        self.get_column = function(column_name){
            for (var index=0; index < self.columns.length; index++)
            {
                var column = self.columns[index];
                if (column.id === column_name)
                    return column;
            }
        };

        self.sort_by_column = function(column){
            if (!column.sortable)
                return;

            //console.log("octolapse.helpers.js - sorting by column:" + column.id);
            var ascending = true;
            if (column.id !== self.sort_column())
            {
                ascending = self.default_sort_direction_ascending;
            }
            else
            {
                ascending = !self.sort_direction_ascending();
            }
            self.sort_direction_ascending(ascending);
            self.sort_column(column.id);
            self.current_page_index(0);
        };

        self.get_current_page_indexes = function(){
            //console.log("octolapse.helpers.js - current page indexes changed");
            if (self.page_size() === 0 || self.list_items().length === 0)
                return null;
            var page_start_index = Math.max(self.current_page_index() * self.page_size(), 0);
            var page_end_index = Math.min(page_start_index + self.page_size(), self.list_items().length);
            return [page_start_index, page_end_index];
        };

        self.list_items_sorted = ko.pureComputed(function() {
            //console.log("octolapse.helpers.js - list items sorting");
            var current_sort_column = self.get_column(self.sort_column());
            if (!current_sort_column)
                return self.list_items();
            var left_direction = self.sort_direction_ascending() ? -1 : 1;
            var right_direction = left_direction * -1;
            var sort_column_id = current_sort_column.sort_column_id;
            return self.list_items().sort(
                function (left, right) {
                    var leftItem = (left.value || {})[sort_column_id] || left[sort_column_id];
                    var rightItem = (right.value || {})[sort_column_id] || right[sort_column_id];
                    return leftItem === rightItem ? 0 : (leftItem < rightItem ? left_direction : right_direction);
                });
        });

        self.current_page = ko.pureComputed(function(){
            //console.log("octolapse.helpers.js - current page changing");
            var page_indexes = self.get_current_page_indexes();
            if (!page_indexes) {
                return[];
            }
            return self.list_items_sorted().slice(page_indexes[0], page_indexes[1]);
        });

        //self.max_page = ko.pureComputed(function(){return Math.floor(self.list_items().length/self.page_size());});

        self._fix_page_numbers = function() {
            //console.log("octolapse.helpers.js - repairing page numbers");
            // Ensure we are not off of any existing pages.  This can happen during a reload, after a delete, or
            // maybe some other scenarios.
            // Make sure we haven't deleted ourselves off the the current page!
            var cur_page = self.current_page_index();
            var has_changed = false;
            if (cur_page + 1 >= self.num_pages())
            {
                has_changed = true;
                cur_page = self.num_pages() - 1;
            }
            if (cur_page < 0)
            {
                has_changed = true;
                cur_page = 0;
            }

            if (has_changed)
                self.current_page_index(cur_page);
        };

        self.set = function(items, on_added){
            self.has_loaded(true);
            var list_items  = [];
            for (var index = 0; index < items.length; index++)
            {
                var list_item = self.to_list_item(items[index]);
                list_items.push(list_item);
                if (on_added)
                {
                    on_added(list_item);
                }
            }
            self.list_items(list_items);
            self._fix_page_numbers();
            self.resize();
        };

        self.clear = function(){
            self.list_items([]);
        };

        self.add = function(item){
            self.has_loaded(true);
            self.list_items.push(self.to_list_item(item));
        };

        self.get = function(id){
            for (var index = 0; index < self.list_items().length; index++)
            {
                if (self.list_items()[index].id === id)
                {
                    return self.list_items()[index];
                }
            }
            return null;
        };

        self.get_index = function(id){
            for (var index = 0; index < self.list_items().length; index++)
            {
                if (self.list_items()[index].id === id)
                {
                    return index;
                }
            }
            return -1;
        };

        self.remove = function(id){
            var item = self.get(id);
            if (item)
            {
                self.list_items.remove(item);
                self._fix_page_numbers();
                return item;
            }
            return null;
        };

        self.replace = function(item){
            var list_item = self.to_list_item(item);
            var index = self.get_index(list_item.id);
            if (index > -1)
            {
                var old_item = self.list_items.splice(index, 1, list_item);
                return old_item[0];
            }
            return null;
        };

        self.select = function(type, selection){
            //console.log("octolapse.helpers.js - selecting " + type);
            // force selection to true or false
            selection = !!selection;
            var page_indexes = null;
            if (type === 'page')
            {
                page_indexes = self.get_current_page_indexes();
            }
            else if (type === 'all')
            {
                if (self.list_items().length > 0)
                {
                    page_indexes = [0, self.list_items().length];
                }
                else {
                    return;
                }
            }

            if (!page_indexes)
            {
                return;
            }
            var list_items_sorted = self.list_items_sorted();
            for (var index=page_indexes[0]; index < page_indexes[1]; index++)
            {
                list_items_sorted[index].selected(selection);
            }
        };

        self.goto_page = function(page_index){
            var num_pages =self.num_pages();
            if (page_index > num_pages - 1)
                page_index = num_pages - 1;

            if (page_index < 0)
                page_index = 0;

            self.current_page_index(page_index);
        };

        self.selected_count = ko.pureComputed(function(){
            var selected_count = 0;
            self.list_items().forEach(function(item, index){
                if (item.selected()) {
                    selected_count++;
                }
            });
            return selected_count;
        });

        self.selected = function(fields_to_return){
            //console.log("octolapse.helpers.js - returning selected items.");
            var selected_items = [];
            for (var index=0; index < self.list_items().length; index++)
            {
                var item = self.list_items()[index];
                if (item.selected()) {
                    if (fields_to_return)
                    {
                        var value = {};
                        fields_to_return.forEach(function(field, index){
                            var is_value_field = false;
                            var field_value = null;
                            if (item[field] === undefined)
                            {
                                is_value_field = true;
                                field_value = item.value[field];
                            }
                            else
                            {
                                field_value = item[field];
                            }
                            if (field_value && (ko.isObservable(field_value) || ko.isComputed(field_value)))
                            {
                                field_value = field_value();
                            }
                            if(is_value_field)
                            {
                                if (!value.value)
                                {
                                    value.value = {};
                                }
                                value.value[field] = field_value;
                            }
                            else{
                                value[field] = field_value;
                            }

                        });
                        selected_items.push(value);
                    }
                    else
                    {
                        selected_items.push(item);
                    }
                }
            }
            return selected_items;
        };

    };

    Octolapse.PagerPageViewModel = function(type, index){
        var self = this;
        self.index = type === 'link'? index : -1;
        self.name = type === 'link' ? (index+1).toString() : "";
        self.type = type;
    };

});
