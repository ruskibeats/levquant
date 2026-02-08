"""Tests for the import panel functionality."""

import json
import pytest
from web.components.import_panel import validate_imported_json, extract_inputs_from_json


def test_validate_imported_json_valid():
    """Test validation with valid JSON structure."""
    data = {
        "inputs": {
            "procedural": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
            "monetary": {},
            "kill_switches": {},
        }
    }
    is_valid, message = validate_imported_json(data)
    assert is_valid is True
    assert message == "Valid"


def test_validate_imported_json_missing_inputs():
    """Test validation with missing inputs key."""
    data = {"procedural": {"SV1a": 0.5}}
    is_valid, message = validate_imported_json(data)
    assert is_valid is False
    assert "inputs" in message


def test_validate_imported_json_missing_procedural():
    """Test validation with missing procedural inputs."""
    data = {"inputs": {"monetary": {}}}
    is_valid, message = validate_imported_json(data)
    assert is_valid is False
    assert "procedural" in message


def test_validate_imported_json_missing_svs():
    """Test validation with missing SV values."""
    data = {"inputs": {"procedural": {"SV1a": 0.5}}}  # Missing SV1b/SV1c
    is_valid, message = validate_imported_json(data)
    assert is_valid is False
    assert "SV1a/SV1b/SV1c" in message


def test_extract_inputs_from_json_complete():
    """Test extraction with complete JSON data."""
    data = {
        "inputs": {
            "procedural": {"SV1a": 0.94, "SV1b": 0.86, "SV1c": 0.75},
            "monetary": {
                "principal_debt_gbp": 100000,
                "claimant_costs_gbp": 500000,
                "defendant_costs_estimate_gbp": 250000,
                "regulatory_exposure_gbp": 2000000,
                "transaction_value_gbp": 0,
                "assumptions_notes": "Test notes",
            },
            "kill_switches": {
                "nullity_confirmed": True,
                "regulatory_open": True,
                "insurer_notice": True,
                "override_admitted": True,
                "shadow_director": True,
            },
            "containment": {
                "containment_exposure_gbp": 20000000,
                "reputational_damage_gbp": 8000000,
                "regulatory_fine_risk_gbp": 4000000,
                "litigation_cascade_risk_gbp": 6000000,
            },
            "stance": {
                "anchor_gbp": 15000000,
                "minimum_objective_gbp": 9000000,
                "objective_mode": "containment",
            },
            "fear_override": 0.75,
        }
    }
    
    extracted = extract_inputs_from_json(data)
    
    # Check procedural
    assert extracted["procedural"].SV1a == 0.94
    assert extracted["procedural"].SV1b == 0.86
    assert extracted["procedural"].SV1c == 0.75
    
    # Check monetary
    assert extracted["monetary"].principal_debt_gbp == 100000
    assert extracted["monetary"].claimant_costs_gbp == 500000
    
    # Check kill switches - all should be True
    assert extracted["kill_switches"].nullity_confirmed is True
    assert extracted["kill_switches"].regulatory_open is True
    assert extracted["kill_switches"].insurer_notice is True
    assert extracted["kill_switches"].override_admitted is True
    assert extracted["kill_switches"].shadow_director is True
    
    # Check containment
    assert extracted["containment"].containment_exposure_gbp == 20000000
    assert extracted["containment"].reputational_damage_gbp == 8000000
    
    # Check stance
    assert extracted["stance"].anchor_gbp == 15000000
    assert extracted["stance"].minimum_objective_gbp == 9000000
    assert extracted["stance"].objective_mode == "containment"
    
    # Check fear override
    assert extracted["fear_override"] == 0.75


def test_extract_inputs_from_json_defaults():
    """Test extraction with minimal JSON data uses defaults."""
    data = {
        "inputs": {
            "procedural": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
        }
    }
    
    extracted = extract_inputs_from_json(data)
    
    # Check defaults
    assert extracted["procedural"].SV1a == 0.5
    assert extracted["monetary"].principal_debt_gbp == 0.0
    assert extracted["kill_switches"].nullity_confirmed is False
    assert extracted["containment"].containment_exposure_gbp == 0.0
    assert extracted["stance"].anchor_gbp == 15000000.0
    assert extracted["fear_override"] is None


def test_extract_inputs_from_json_no_fear_override():
    """Test extraction when fear_override is not in JSON."""
    data = {
        "inputs": {
            "procedural": {"SV1a": 0.5, "SV1b": 0.6, "SV1c": 0.7},
            "fear_override": None,
        }
    }
    
    extracted = extract_inputs_from_json(data)
    assert extracted["fear_override"] is None


def test_full_run_json_structure():
    """Test with realistic full_run JSON structure."""
    data = {
        "inputs": {
            "procedural": {"SV1a": 0.94, "SV1b": 0.86, "SV1c": 0.75},
            "monetary": {
                "principal_debt_gbp": 66000,
                "claimant_costs_gbp": 500000,
                "defendant_costs_estimate_gbp": 250000,
                "regulatory_exposure_gbp": 5000000,
                "transaction_value_gbp": 0,
                "assumptions_notes": "Test scenario",
            },
            "kill_switches": {
                "nullity_confirmed": True,
                "regulatory_open": True,
                "insurer_notice": True,
                "override_admitted": False,
                "shadow_director": False,
            },
            "containment": {
                "containment_exposure_gbp": 20000000,
                "reputational_damage_gbp": 8000000,
                "regulatory_fine_risk_gbp": 4000000,
                "litigation_cascade_risk_gbp": 6000000,
            },
            "stance": {
                "anchor_gbp": 15000000,
                "minimum_objective_gbp": 9000000,
                "objective_mode": "containment",
            },
            "fear_override": 0.75,
        },
        "engine": {
            "upls": 0.865,
            "decision": "ACCEPT",
            "confidence": "Strong",
            "tripwire": 9.5,
        },
        "fear_index": 0.75,
    }
    
    # Should validate successfully
    is_valid, message = validate_imported_json(data)
    assert is_valid is True
    
    # Should extract correctly
    extracted = extract_inputs_from_json(data)
    assert extracted["fear_override"] == 0.75
    assert extracted["stance"].objective_mode == "containment"
