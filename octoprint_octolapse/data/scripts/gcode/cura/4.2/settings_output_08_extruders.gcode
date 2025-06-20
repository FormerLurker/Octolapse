; Script based on an original created by tjjfvi (https://github.com/tjjfvi)
; An up-to-date version of the tjjfvi's original script can be found
; here:  https://csi.t6.fyi/
; Note - This script will only work in Cura V4.2 and above!
; --- Global Settings
; layer_height = {layer_height}
; smooth_spiralized_contours = {smooth_spiralized_contours}
; magic_mesh_surface_mode = {magic_mesh_surface_mode}
; machine_extruder_count = {machine_extruder_count}
; --- Single Extruder Settings
; speed_z_hop = {speed_z_hop}
; retraction_amount = {retraction_amount}
; retraction_hop = {retraction_hop}
; retraction_hop_enabled = {retraction_hop_enabled}
; retraction_enable = {retraction_enable}
; retraction_speed = {retraction_speed}
; retraction_retract_speed = {retraction_retract_speed}
; retraction_prime_speed = {retraction_prime_speed}
; speed_travel = {speed_travel}
; --- Multi-Extruder Settings
; speed_z_hop_0 = {speed_z_hop, 0}
; speed_z_hop_1 = {speed_z_hop, 1}
; speed_z_hop_2 = {speed_z_hop, 2}
; speed_z_hop_3 = {speed_z_hop, 3}
; speed_z_hop_4 = {speed_z_hop, 4}
; speed_z_hop_5 = {speed_z_hop, 5}
; speed_z_hop_6 = {speed_z_hop, 6}
; speed_z_hop_7 = {speed_z_hop, 7}
; retraction_amount_0 = {retraction_amount, 0}
; retraction_amount_1 = {retraction_amount, 1}
; retraction_amount_2 = {retraction_amount, 2}
; retraction_amount_3 = {retraction_amount, 3}
; retraction_amount_4 = {retraction_amount, 4}
; retraction_amount_5 = {retraction_amount, 5}
; retraction_amount_6 = {retraction_amount, 6}
; retraction_amount_7 = {retraction_amount, 7}
; retraction_hop_0 = {retraction_hop, 0}
; retraction_hop_1 = {retraction_hop, 1}
; retraction_hop_2 = {retraction_hop, 2}
; retraction_hop_3 = {retraction_hop, 3}
; retraction_hop_4 = {retraction_hop, 4}
; retraction_hop_5 = {retraction_hop, 5}
; retraction_hop_6 = {retraction_hop, 6}
; retraction_hop_7 = {retraction_hop, 7}
; retraction_hop_enabled_0 = {retraction_hop_enabled, 0}
; retraction_hop_enabled_1 = {retraction_hop_enabled, 1}
; retraction_hop_enabled_2 = {retraction_hop_enabled, 2}
; retraction_hop_enabled_3 = {retraction_hop_enabled, 3}
; retraction_hop_enabled_4 = {retraction_hop_enabled, 4}
; retraction_hop_enabled_5 = {retraction_hop_enabled, 5}
; retraction_hop_enabled_6 = {retraction_hop_enabled, 6}
; retraction_hop_enabled_7 = {retraction_hop_enabled, 7}
; retraction_prime_speed_0 = {retraction_prime_speed, 0}
; retraction_prime_speed_1 = {retraction_prime_speed, 1}
; retraction_prime_speed_2 = {retraction_prime_speed, 2}
; retraction_prime_speed_3 = {retraction_prime_speed, 3}
; retraction_prime_speed_4 = {retraction_prime_speed, 4}
; retraction_prime_speed_5 = {retraction_prime_speed, 5}
; retraction_prime_speed_6 = {retraction_prime_speed, 6}
; retraction_prime_speed_7 = {retraction_prime_speed, 7}
; retraction_retract_speed_0 = {retraction_retract_speed, 0}
; retraction_retract_speed_1 = {retraction_retract_speed, 1}
; retraction_retract_speed_2 = {retraction_retract_speed, 2}
; retraction_retract_speed_3 = {retraction_retract_speed, 3}
; retraction_retract_speed_4 = {retraction_retract_speed, 4}
; retraction_retract_speed_5 = {retraction_retract_speed, 5}
; retraction_retract_speed_6 = {retraction_retract_speed, 6}
; retraction_retract_speed_7 = {retraction_retract_speed, 7}
; retraction_speed_0 = {retraction_speed, 0}
; retraction_speed_1 = {retraction_speed, 1}
; retraction_speed_2 = {retraction_speed, 2}
; retraction_speed_3 = {retraction_speed, 3}
; retraction_speed_4 = {retraction_speed, 4}
; retraction_speed_5 = {retraction_speed, 5}
; retraction_speed_6 = {retraction_speed, 6}
; retraction_speed_7 = {retraction_speed, 7}
; retraction_enable_0 = {retraction_enable, 0}
; retraction_enable_1 = {retraction_enable, 1}
; retraction_enable_2 = {retraction_enable, 2}
; retraction_enable_3 = {retraction_enable, 3}
; retraction_enable_4 = {retraction_enable, 4}
; retraction_enable_5 = {retraction_enable, 5}
; retraction_enable_6 = {retraction_enable, 6}
; retraction_enable_7 = {retraction_enable, 7}
; speed_travel_0 = {speed_travel, 0}
; speed_travel_1 = {speed_travel, 1}
; speed_travel_2 = {speed_travel, 2}
; speed_travel_3 = {speed_travel, 3}
; speed_travel_4 = {speed_travel, 4}
; speed_travel_5 = {speed_travel, 5}
; speed_travel_6 = {speed_travel, 6}
; speed_travel_7 = {speed_travel, 7}


