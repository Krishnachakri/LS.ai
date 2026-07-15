from .context_parser import ParsedEmergencyContext
from ..schemas import IncidentType

class EmergencyContextValidator:
    @staticmethod
    def validate_and_sanitize(context: ParsedEmergencyContext) -> ParsedEmergencyContext:
        """
        Validates the extracted emergency context and sanitizes fields to maintain data integrity.
        
        Ensures:
          1. Victim count is clamped to a minimum of 1.
          2. Incident Type is matched to the schema's allowed category enums.
        """
        # Clamp victim count to at least 1
        sanitized_victim_count = max(1, context.victim_count)
        
        # Ensure incident type matches enums
        sanitized_type = context.incident_type
        if sanitized_type not in [IncidentType.ROAD_ACCIDENT, IncidentType.MEDICAL, IncidentType.UNKNOWN]:
            sanitized_type = IncidentType.MEDICAL # default fallback if unknown is somehow selected
            
        return ParsedEmergencyContext(
            incident_type=sanitized_type,
            victim_count=sanitized_victim_count,
            structured_facts=context.structured_facts
        )
