#include "gcode_comment_processor.h"

gcode_comment_processor::gcode_comment_processor()
{
	current_section_ = no_section;
	processing_type_ = unknown;
}

gcode_comment_processor::~gcode_comment_processor()
{
}

void gcode_comment_processor::update(position& pos)
{
	if (processing_type_ == OFF)
		return;

	if (current_section_ != no_section)
	{
		update_feature_from_section(pos);
		return;
	}		

	if (processing_type_ == unknown || processing_type_ == slic3r_pe)
	{
		if (update_feature_for_slic3r_pe_comment(pos, pos.p_command.comment_))
			processing_type_ = slic3r_pe;
	}
	
}

bool gcode_comment_processor::update_feature_for_slic3r_pe_comment(position& pos, std::string &comment) const
{
	if (comment == "perimeter" || comment == "move to first perimeter point")
	{
		pos.feature_type_tag_ = unknown_perimeter_feature;
		return true;
	}
	if (comment == "infill" || comment == "move to first infill point")
	{
		pos.feature_type_tag_ = infill_feature;
		return true;
	}
	if (comment == "infill(bridge)" || comment == "move to first infill(bridge) point")
	{
		pos.feature_type_tag_ = bridge_feature;
		return true;
	}
	if (comment == "skirt" || comment == "move to first skirt point")
	{
		pos.feature_type_tag_ = skirt_feature;
		return true;
	}
	return false;
}

void gcode_comment_processor::update_feature_from_section(position& pos)
{
	if (processing_type_ == OFF || current_section_ == no_section)
		return;

	switch (current_section_)
	{
	case(outer_perimeter_section):
		pos.feature_type_tag_ = outer_perimeter_feature;
		break;
	case(inner_perimeter_section):
		pos.feature_type_tag_ = inner_perimeter_feature;
		break;
	case(skirt_section):
		pos.feature_type_tag_ = skirt_feature;
		break;
	case(solid_infill_section):
		pos.feature_type_tag_ = solid_infill_feature;
		break;
	case(ooze_shield_section):
		pos.feature_type_tag_ = ooze_shield_feature;
		break;
	case(infill_section):
		pos.feature_type_tag_ = infill_feature;
		break;
	case(prime_pillar_section):
		pos.feature_type_tag_ = prime_pillar_feature;
		break;
	}
}

void gcode_comment_processor::update(std::string & comment)
{
	switch(processing_type_)
	{
	case OFF:
		break;
	case unknown:
		update_unknown_section(comment);
		break;
	case cura:
		update_cura_section(comment);
		break;
	case slic3r_pe:
		update_slic3r_pe_section(comment);
		break;
	case simplify_3d:
		update_simplify_3d_section(comment);
		break;
	}
}

void gcode_comment_processor::update_unknown_section(std::string & comment)
{
	if (update_cura_section(comment))
	{
		processing_type_ = cura;
		return;
	}
		
	if (update_simplify_3d_section(comment))
	{
		processing_type_ = simplify_3d;
		return;
	}
	if(update_slic3r_pe_section(comment))
	{
		processing_type_ = slic3r_pe;
		return;
	}
}

bool gcode_comment_processor::update_cura_section(std::string &comment)
{
	if (comment == "TYPE:WALL-OUTER")
	{
		current_section_ = outer_perimeter_section;
		return true;
	}
	else if (comment == "TYPE:WALL-INNER")
	{
		current_section_ = inner_perimeter_section;
		return true;
	}
	if (comment == "TYPE:FILL")
	{
		current_section_ = infill_section;
		return true;
	}
	if (comment.rfind("LAYER:", 0))
	{
		current_section_ = no_section;
		return false;
	}
	if (comment == "TYPE:SKIRT")
	{
		current_section_ = skirt_section;
		return true;
	}
	return false;
}

bool gcode_comment_processor::update_simplify_3d_section(std::string &comment)
{
	if (comment == "outer perimeter")
	{
		current_section_ = outer_perimeter_section;
		return true;
	}
	if (comment == "inner perimeter")
	{
		current_section_ = inner_perimeter_section;
		return true;
	}
	if (comment == "infill")
	{
		current_section_ = infill_section;
		return true;
	}
	if (comment == "solid layer")
	{
		current_section_ = solid_infill_section;
		return true;
	}
	if (comment == "skirt")
	{
		current_section_ = skirt_section;
		return true;
	}
	if (comment == "ooze shield")
	{
		current_section_ = ooze_shield_section;
		return true;
	}
	if (comment == "skirt")
	{
		current_section_ = skirt_section;
		return true;
	}
	if (comment == "prime pillar")
	{
		current_section_ = skirt_section;
		return true;
	}
	
	return false;
}

bool gcode_comment_processor::update_slic3r_pe_section(std::string &comment)
{
	if (comment == "CP TOOLCHANGE WIPE")
	{
		current_section_ = prime_pillar_section;
		return true;
	}
	if (comment == "CP TOOLCHANGE END")
	{
		current_section_ = no_section;
		return true;
	}
	return false;
}

