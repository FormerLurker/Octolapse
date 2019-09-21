#include "gcode_comment_processor.h"

gcode_comment_processor::gcode_comment_processor()
{
	current_section_ = section_type_no_section;
	processing_type_ = comment_process_type_unknown;
}

gcode_comment_processor::~gcode_comment_processor()
{
}

comment_process_type gcode_comment_processor::get_comment_process_type()
{
	return processing_type_;
}

void gcode_comment_processor::update(position& pos)
{
	if (processing_type_ == comment_process_type_off)
		return;

	if (current_section_ != section_type_no_section)
	{
		update_feature_from_section(pos);
		return;
	}		

	if (processing_type_ == comment_process_type_unknown || processing_type_ == comment_process_type_slic3r_pe)
	{
		if (update_feature_for_slic3r_pe_comment(pos, pos.command.comment))
			processing_type_ = comment_process_type_slic3r_pe;
	}
	
}

bool gcode_comment_processor::update_feature_for_slic3r_pe_comment(position& pos, std::string &comment) const
{
	if (comment == "perimeter" || comment == "move to first perimeter point")
	{
		pos.feature_type_tag = feature_type_unknown_perimeter_feature;
		return true;
	}
	if (comment == "infill" || comment == "move to first infill point")
	{
		pos.feature_type_tag = feature_type_infill_feature;
		return true;
	}
	if (comment == "infill(bridge)" || comment == "move to first infill(bridge) point")
	{
		pos.feature_type_tag = feature_type_bridge_feature;
		return true;
	}
	if (comment == "skirt" || comment == "move to first skirt point")
	{
		pos.feature_type_tag = feature_type_skirt_feature;
		return true;
	}
	return false;
}

void gcode_comment_processor::update_feature_from_section(position& pos) const
{
	if (processing_type_ == comment_process_type_off || current_section_ == section_type_no_section)
		return;

	switch (current_section_)
	{
	case(section_type_outer_perimeter_section):
		pos.feature_type_tag = feature_type_outer_perimeter_feature;
		break;
	case(section_type_inner_perimeter_section):
		pos.feature_type_tag = feature_type_inner_perimeter_feature;
		break;
	case(section_type_skirt_section):
		pos.feature_type_tag = feature_type_skirt_feature;
		break;
	case(section_type_solid_infill_section):
		pos.feature_type_tag = feature_type_solid_infill_feature;
		break;
	case(section_type_ooze_shield_section):
		pos.feature_type_tag = feature_type_ooze_shield_feature;
		break;
	case(section_type_infill_section):
		pos.feature_type_tag = feature_type_infill_feature;
		break;
	case(section_type_prime_pillar_section):
		pos.feature_type_tag = feature_type_prime_pillar_feature;
		break;
	case(section_type_gap_fill_section):
		pos.feature_type_tag = feature_type_gap_fill_feature;
	}
}

void gcode_comment_processor::update(std::string & comment)
{
	switch(processing_type_)
	{
	case comment_process_type_off:
		break;
	case comment_process_type_unknown:
		update_unknown_section(comment);
		break;
	case comment_process_type_cura:
		update_cura_section(comment);
		break;
	case comment_process_type_slic3r_pe:
		update_slic3r_pe_section(comment);
		break;
	case comment_process_type_simplify_3d:
		update_simplify_3d_section(comment);
		break;
	}
}

void gcode_comment_processor::update_unknown_section(std::string & comment)
{
	if (comment.length() == 0)
		return;

	if (update_cura_section(comment))
	{
		processing_type_ = comment_process_type_cura;
		return;
	}
		
	if (update_simplify_3d_section(comment))
	{
		processing_type_ = comment_process_type_simplify_3d;
		return;
	}
	if(update_slic3r_pe_section(comment))
	{
		processing_type_ = comment_process_type_slic3r_pe;
		return;
	}
}

bool gcode_comment_processor::update_cura_section(std::string &comment)
{
	if (comment == "TYPE:WALL-OUTER")
	{
		current_section_ = section_type_outer_perimeter_section;
		return true;
	}
	else if (comment == "TYPE:WALL-INNER")
	{
		current_section_ = section_type_inner_perimeter_section;
		return true;
	}
	if (comment == "TYPE:FILL")
	{
		current_section_ = section_type_infill_section;
		return true;
	}
	if (comment == "TYPE:SKIN")
	{
		current_section_ = section_type_solid_infill_section;
		return true;
	}
	if (comment.rfind("LAYER:", 0) != std::string::npos || comment.rfind(";MESH:NONMESH", 0) != std::string::npos)
	{
		current_section_ = section_type_no_section;
		return false;
	}
	if (comment == "TYPE:SKIRT")
	{
		current_section_ = section_type_skirt_section;
		return true;
	}
	return false;
}

bool gcode_comment_processor::update_simplify_3d_section(std::string &comment)
{
	// Apparently simplify 3d added the word 'feature' to the their feature comments
	// at some point to make my life more difficult :P
	if (comment.rfind("feature", 0) != std::string::npos)
	{
		if (comment == "feature outer perimeter")
		{
			current_section_ = section_type_outer_perimeter_section;
			return true;
		}
		if (comment == "feature inner perimeter")
		{
			current_section_ = section_type_inner_perimeter_section;
			return true;
		}
		if (comment == "feature infill")
		{
			current_section_ = section_type_infill_section;
			return true;
		}
		if (comment == "feature solid layer")
		{
			current_section_ = section_type_solid_infill_section;
			return true;
		}
		if (comment == "feature skirt")
		{
			current_section_ = section_type_skirt_section;
			return true;
		}
		if (comment == "feature ooze shield")
		{
			current_section_ = section_type_ooze_shield_section;
			return true;
		}
		if (comment == "feature prime pillar")
		{
			current_section_ = section_type_prime_pillar_section;
			return true;
		}
		if (comment == "feature gap fill")
		{
			current_section_ = section_type_gap_fill_section;
			return true;
		}
	}
	else
	{
		if (comment == "outer perimeter")
		{
			current_section_ = section_type_outer_perimeter_section;
			return true;
		}
		if (comment == "inner perimeter")
		{
			current_section_ = section_type_inner_perimeter_section;
			return true;
		}
		if (comment == "infill")
		{
			current_section_ = section_type_infill_section;
			return true;
		}
		if (comment == "solid layer")
		{
			current_section_ = section_type_solid_infill_section;
			return true;
		}
		if (comment == "skirt")
		{
			current_section_ = section_type_skirt_section;
			return true;
		}
		if (comment == "ooze shield")
		{
			current_section_ = section_type_ooze_shield_section;
			return true;
		}

		if (comment == "prime pillar")
		{
			current_section_ = section_type_prime_pillar_section;
			return true;
		}

		if (comment == "gap fill")
		{
			current_section_ = section_type_gap_fill_section;
			return true;
		}
	}
	
	
	return false;
}

bool gcode_comment_processor::update_slic3r_pe_section(std::string &comment)
{
	if (comment == "CP TOOLCHANGE WIPE")
	{
		current_section_ = section_type_prime_pillar_section;
		return true;
	}
	if (comment == "CP TOOLCHANGE END")
	{
		current_section_ = section_type_no_section;
		return true;
	}
	return false;
}

