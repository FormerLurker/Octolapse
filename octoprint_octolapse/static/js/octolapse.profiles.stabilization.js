/// Create our stabilizations view model
$(function() {
    Octolapse.StabilizationProfileViewModel = function (values) {
        self = this
        self.name = ko.observable(values.name);
        self.guid = ko.observable(values.guid);
        self.x_type = ko.observable(values.x_type);
        self.x_fixed_coordinate = ko.observable(values.x_fixed_coordinate);
        self.x_fixed_path = ko.observable(values.x_fixed_path);
        self.x_fixed_path_loop = ko.observable(values.x_fixed_path_loop);
        self.x_fixed_path_invert_loop = ko.observable(values.x_fixed_path_invert_loop);
        self.x_relative = ko.observable(values.x_relative);
        self.x_relative_print = ko.observable(values.x_relative_print);
        self.x_relative_path = ko.observable(values.x_relative_path);
        self.x_relative_path_loop = ko.observable(values.x_relative_path_loop);
        self.x_relative_path_invert_loop = ko.observable(values.x_relative_path_invert_loop);
        self.y_type = ko.observable(values.y_type);
        self.y_fixed_coordinate = ko.observable(values.y_fixed_coordinate);
        self.y_fixed_path = ko.observable(values.y_fixed_path);
        self.y_fixed_path_loop = ko.observable(values.y_fixed_path_loop);
        self.y_fixed_path_invert_loop = ko.observable(values.y_fixed_path_invert_loop);
        self.y_relative = ko.observable(values.y_relative);
        self.y_relative_print = ko.observable(values.y_relative_print);
        self.y_relative_path = ko.observable(values.y_relative_path);
        self.y_relative_path_loop = ko.observable(values.y_relative_path_loop);
        self.y_relative_path_invert_loop = ko.observable(values.y_relative_path_invert_loop);
    };

    Octolapse.StabilizationProfileValidationRules = {
        rules: {
            name: "required"
            ,x_type: "required"
            ,x_fixed_coordinate: { number: true, required: true }
            , x_fixed_path: { required: true, csvFloat: true}
            , x_relative: { required: true, number: true,min:0.0, max:100.0 }
            , x_relative_path: { required: true, csvRelative: true }
            , y_type: "required"
            , y_fixed_coordinate: { number: true, required: true }
            , y_fixed_path: { required: true, csvFloat: true }
            , y_relative: { required: true, number: true, min: 0.0, max: 100.0 }
            , y_relative_path: { required: true, csvRelative: true }

        },
        messages: {
            name: "Please enter a name for your profile",
        }
    };
});


