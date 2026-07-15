import sys
import os
import time

# Ensure Windows console supports Telugu characters in print statements
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.context_parser import EmergencyContextParser, ParserException
from app.services.validator import EmergencyContextValidator
from app.services.severity_rubric import evaluate_incident_severity

def test_integration():
    """
    Test script to run the parser + validator + severity engine end-to-end.
    """
    # 3 sample emergency transcripts
    test_cases = [
        {
            "name": "English Road Accident (Urgent)",
            "text": "A car just hit a pole. The driver is conscious, but he says his leg is broken and he cannot move."
        },
        {
            "name": "Telugu Cardiac/Respiratory (Critical)",
            "text": "నాకు చాతి నొప్పిగా ఉంది, శ్వాస తీసుకోవడం చాలా కష్టంగా ఉంది, దయచేసి వెంటనే సహాయం చేయండి."
        },
        {
            "name": "Mixed Multi-Victim Incident (Critical)",
            "text": "Please send help! ఇక్కడ ఒక కార్ యాక్సిడెంట్ జరిగింది. There are three people inside. Two are bleeding heavily, and one is not waking up!"
        }
    ]

    try:
        parser = EmergencyContextParser()
    except Exception as e:
        print(f"[ERROR] Failed to initialize parser (Check OPENAI_API_KEY): {e}")
        return

    print("======================================================================")
    print("                INTEGRATED PARSER & SEVERITY TEST                      ")
    print("======================================================================\n")

    for i, case in enumerate(test_cases, 1):
        print(f"--- TEST CASE {i}: {case['name']} ---")
        print(f"Input Text: \"{case['text']}\"\n")
        
        try:
            # 1. Parse Context & extract time
            parsed_context, elapsed_ms = parser.parse_transcript(case["text"])
            
            # 2. Validate
            validated_context = EmergencyContextValidator.validate_and_sanitize(parsed_context)
            
            # 3. Evaluate Severity
            severity_result = evaluate_incident_severity(validated_context.structured_facts, validated_context.victim_count)
            
            print(f"Parser Time:       {elapsed_ms} ms")
            print(f"Incident Type:     {validated_context.incident_type.value}")
            print(f"Victim Count:      {validated_context.victim_count}")
            print(f"Structured Facts:  {validated_context.structured_facts.model_dump()}")
            print(f"Severity:          {severity_result.severity.value}")
            print(f"Severity Score:    {severity_result.score}")
            print(f"Severity Reason:   \"{severity_result.reason}\"")
            
        except ParserException as e:
            print(f"[PARSER ERROR] Case {i} failed: {e}")
        except Exception as e:
            print(f"[ERROR] Case {i} failed: {e}")
            
        print("-" * 70 + "\n")

if __name__ == "__main__":
    test_integration()
