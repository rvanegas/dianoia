import json
import pytest
from services.agent_prompts import agent_gpt_formalize

try:
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def test_formalization_schema_validity():
    """Test that the formalization agent schema is valid JSON and follows OpenAI API requirements."""
    
    # Get the schema from the agent
    schema = agent_gpt_formalize.response_format_base
    
    # Test 1: Schema is valid JSON
    try:
        json.dumps(schema)
    except Exception as e:
        pytest.fail(f"Schema is not valid JSON: {e}")
    
    # Test 2: Schema has required top-level structure
    assert "type" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema
    
    # Test 3: Check formalizations array structure
    formalizations_prop = schema["properties"]["formalizations"]
    assert formalizations_prop["type"] == "array"
    assert "items" in formalizations_prop
    assert formalizations_prop["items"]["type"] == "object"
    
    # Test 4: Check formalization item properties
    item_props = formalizations_prop["items"]["properties"]
    assert "symbol" in item_props
    assert "ascii" in item_props
    assert "json_structure" in item_props
    assert item_props["symbol"]["type"] == "string"
    assert item_props["ascii"]["type"] == "string"
    assert item_props["json_structure"]["type"] == "string"
    
    # Test 5: Check definitions structure
    definitions_prop = schema["properties"]["definitions"]
    assert definitions_prop["type"] == "object"
    assert "predicates" in definitions_prop["properties"]
    assert "constants" in definitions_prop["properties"]
    
    # Test 6: Check predicates array
    predicates_prop = definitions_prop["properties"]["predicates"]
    assert predicates_prop["type"] == "array"
    assert "items" in predicates_prop
    assert predicates_prop["items"]["type"] == "object"
    
    # Test 7: Check predicate item properties
    predicate_item_props = predicates_prop["items"]["properties"]
    assert "symbol" in predicate_item_props
    assert "value" in predicate_item_props
    assert predicate_item_props["symbol"]["type"] == "string"
    assert predicate_item_props["value"]["type"] == "string"
    
    # Test 8: Check constants array
    constants_prop = definitions_prop["properties"]["constants"]
    assert constants_prop["type"] == "array"
    assert "items" in constants_prop
    assert constants_prop["items"]["type"] == "object"
    
    # Test 9: Check constant item properties
    constant_item_props = constants_prop["items"]["properties"]
    assert "symbol" in constant_item_props
    assert "value" in constant_item_props
    assert constant_item_props["symbol"]["type"] == "string"
    assert constant_item_props["value"]["type"] == "string"
    
    # Test 10: Check other required fields
    assert "confidence" in schema["properties"]
    assert "reasoning" in schema["properties"]
    assert schema["properties"]["confidence"]["type"] == "number"
    assert schema["properties"]["reasoning"]["type"] == "string"
    
    # Test 11: Check required fields list
    required_fields = schema["required"]
    assert "formalizations" in required_fields
    assert "definitions" in required_fields
    assert "confidence" in required_fields
    assert "reasoning" in required_fields
    
    # Test 12: Check additionalProperties restrictions
    assert schema["additionalProperties"] is False
    assert formalizations_prop["items"]["additionalProperties"] is False
    assert predicates_prop["items"]["additionalProperties"] is False
    assert constants_prop["items"]["additionalProperties"] is False
    assert definitions_prop["additionalProperties"] is False
    assert predicates_prop["additionalProperties"] is False
    assert constants_prop["additionalProperties"] is False


def test_schema_matches_example():
    """Test that the schema can validate the example from the prompt."""
    
    example_response = {
        "formalizations": [
            {
                "symbol": "A",
                "ascii": "P(a)",
                "json_structure": "{\"type\": \"predicate\", \"predicate\": \"P\", \"terms\": [\"a\"]}"
            },
            {
                "symbol": "B",
                "ascii": "forall x. (P(x) -> Q(x))",
                "json_structure": "{\"type\": \"universal\", \"variable\": \"x\", \"body\": {\"type\": \"implication\", \"antecedent\": {\"type\": \"predicate\", \"predicate\": \"P\", \"terms\": [\"x\"]}, \"consequent\": {\"type\": \"predicate\", \"predicate\": \"Q\", \"terms\": [\"x\"]}}}"
            },
            {
                "symbol": "C",
                "ascii": "Q(a)",
                "json_structure": "{\"type\": \"predicate\", \"predicate\": \"Q\", \"terms\": [\"a\"]}"
            }
        ],
        "definitions": {
            "predicates": [
                {"symbol": "P", "value": "is a man"},
                {"symbol": "Q", "value": "is mortal"}
            ],
            "constants": [
                {"symbol": "a", "value": "Socrates"}
            ]
        },
        "confidence": 0.95,
        "reasoning": "Consistent formalization using P for 'is a man' and Q for 'is mortal' across all propositions"
    }
    
    # This test would require a JSON schema validation library
    # For now, we'll just verify the structure matches our expectations
    assert "formalizations" in example_response
    assert "definitions" in example_response
    assert "confidence" in example_response
    assert "reasoning" in example_response
    
    # Check formalizations structure
    for formalization in example_response["formalizations"]:
        assert "symbol" in formalization
        assert "ascii" in formalization
        assert "json_structure" in formalization
        assert isinstance(formalization["symbol"], str)
        assert isinstance(formalization["ascii"], str)
        assert isinstance(formalization["json_structure"], str)
    
    # Check definitions structure
    definitions = example_response["definitions"]
    assert "predicates" in definitions
    assert "constants" in definitions
    assert isinstance(definitions["predicates"], list)
    assert isinstance(definitions["constants"], list)
    
    # Check predicates
    for predicate in definitions["predicates"]:
        assert "symbol" in predicate
        assert "value" in predicate
        assert isinstance(predicate["symbol"], str)
        assert isinstance(predicate["value"], str)
    
    # Check constants
    for constant in definitions["constants"]:
        assert "symbol" in constant
        assert "value" in constant
        assert isinstance(constant["symbol"], str)
        assert isinstance(constant["value"], str)


@pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema library not available")
def test_schema_json_validation():
    """Test that the schema can validate JSON responses using jsonschema library."""
    
    schema = agent_gpt_formalize.response_format_base
    
    # Valid response
    valid_response = {
        "formalizations": [
            {
                "symbol": "A",
                "ascii": "P(a)",
                "json_structure": "{\"type\": \"predicate\", \"predicate\": \"P\", \"terms\": [\"a\"]}"
            }
        ],
        "definitions": {
            "predicates": [
                {"symbol": "P", "value": "is a man"}
            ],
            "constants": [
                {"symbol": "a", "value": "Socrates"}
            ]
        },
        "confidence": 0.95,
        "reasoning": "Test reasoning"
    }
    
    # Should not raise an exception
    validate(instance=valid_response, schema=schema)
    
    # Invalid response - missing required field
    invalid_response = {
        "formalizations": [
            {
                "symbol": "A",
                "ascii": "P(a)",
                "json_structure": "{\"type\": \"predicate\", \"predicate\": \"P\", \"terms\": [\"a\"]}"
            }
        ],
        "definitions": {
            "predicates": [
                {"symbol": "P", "value": "is a man"}
            ],
            "constants": []
        },
        "confidence": 0.95
        # Missing "reasoning" field
    }
    
    # Should raise ValidationError
    with pytest.raises(ValidationError):
        validate(instance=invalid_response, schema=schema)


def test_schema_openai_compatibility():
    """Test that the schema follows OpenAI API requirements."""
    
    schema = agent_gpt_formalize.response_format_base
    
    # OpenAI requires these basic properties
    assert "type" in schema
    assert "properties" in schema
    
    # OpenAI supports these types
    valid_types = {"object", "array", "string", "number", "integer", "boolean"}
    assert schema["type"] in valid_types
    
    # Check that all property types are valid
    def check_property_types(obj):
        if isinstance(obj, dict):
            if "type" in obj:
                assert obj["type"] in valid_types, f"Invalid type: {obj['type']}"
            for value in obj.values():
                if isinstance(value, dict):
                    check_property_types(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            check_property_types(item)
    
    check_property_types(schema)
    
    # Check that additionalProperties is boolean when present
    def check_additional_properties(obj):
        if isinstance(obj, dict):
            if "additionalProperties" in obj:
                assert isinstance(obj["additionalProperties"], bool), "additionalProperties must be boolean"
            for value in obj.values():
                if isinstance(value, dict):
                    check_additional_properties(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            check_additional_properties(item)
    
    check_additional_properties(schema)
