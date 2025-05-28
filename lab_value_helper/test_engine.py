#!/usr/bin/env python3
"""
Test script for the Clinical Significance Engine
Validates the core logic for each lab test
"""

from app import ClinicalSignificanceEngine

def test_hemoglobin_logic():
    """Test hemoglobin evaluation logic"""
    engine = ClinicalSignificanceEngine()
    
    print("=== Hemoglobin Tests ===")
    
    # Female tests
    test_cases = [
        ("Female, 30y, Hgb 11.8", "hemoglobin", 11.8, {"sex": "female", "age": 30}),
        ("Female, 30y, Hgb 9.5", "hemoglobin", 9.5, {"sex": "female", "age": 30}),
        ("Female, 30y, Hgb 6.5", "hemoglobin", 6.5, {"sex": "female", "age": 30}),
        ("Female, 30y, Hgb 12.5", "hemoglobin", 12.5, {"sex": "female", "age": 30}),
        
        # Male tests
        ("Male, 35y, Hgb 13.2", "hemoglobin", 13.2, {"sex": "male", "age": 35}),
        ("Male, 35y, Hgb 12.5", "hemoglobin", 12.5, {"sex": "male", "age": 35}),
        ("Male, 35y, Hgb 14.5", "hemoglobin", 14.5, {"sex": "male", "age": 35}),
        
        # Critical values
        ("Critical low", "hemoglobin", 6.0, {"sex": "female", "age": 30}),
        ("Critical high", "hemoglobin", 19.0, {"sex": "male", "age": 35}),
    ]
    
    for description, test_name, value, context in test_cases:
        result = engine.evaluate_lab_value(test_name, value, context)
        print(f"{description}: {result['significance']} - {result['clinical_pearl']}")
    
    print()

def test_potassium_logic():
    """Test potassium evaluation logic"""
    engine = ClinicalSignificanceEngine()
    
    print("=== Potassium Tests ===")
    
    test_cases = [
        ("Normal K", "potassium", 4.0, {}),
        ("Borderline low", "potassium", 3.3, {}),
        ("Borderline high", "potassium", 5.2, {}),
        ("Clinically low", "potassium", 2.8, {}),
        ("Clinically high", "potassium", 5.8, {}),
        ("Critical low", "potassium", 2.2, {}),
        ("Critical high", "potassium", 6.5, {}),
    ]
    
    for description, test_name, value, context in test_cases:
        result = engine.evaluate_lab_value(test_name, value, context)
        print(f"{description} ({value}): {result['significance']} - {result['clinical_pearl']}")
    
    print()

def test_glucose_logic():
    """Test glucose evaluation logic"""
    engine = ClinicalSignificanceEngine()
    
    print("=== Glucose Tests ===")
    
    test_cases = [
        ("Fasting normal", "glucose", 95, {"fasting": True}),
        ("Fasting prediabetic", "glucose", 110, {"fasting": True}),
        ("Fasting diabetic", "glucose", 140, {"fasting": True}),
        ("Random normal", "glucose", 120, {"fasting": False}),
        ("Random diabetic", "glucose", 220, {"fasting": False}),
        ("Hypoglycemic", "glucose", 45, {}),
        ("Severe hyperglycemic", "glucose", 450, {}),
    ]
    
    for description, test_name, value, context in test_cases:
        result = engine.evaluate_lab_value(test_name, value, context)
        print(f"{description} ({value}): {result['significance']} - {result['clinical_pearl']}")
    
    print()

def test_creatinine_logic():
    """Test creatinine evaluation logic"""
    engine = ClinicalSignificanceEngine()
    
    print("=== Creatinine Tests ===")
    
    test_cases = [
        ("Female, young, normal", "creatinine", 0.9, {"sex": "female", "age": 30}),
        ("Female, elderly, normal", "creatinine", 1.2, {"sex": "female", "age": 75}),
        ("Male, normal", "creatinine", 1.1, {"sex": "male", "age": 35}),
        ("Mild elevation", "creatinine", 1.6, {"sex": "male", "age": 35}),
        ("Significant elevation", "creatinine", 2.5, {"sex": "female", "age": 30}),
        ("Critical elevation", "creatinine", 4.5, {"sex": "male", "age": 45}),
    ]
    
    for description, test_name, value, context in test_cases:
        result = engine.evaluate_lab_value(test_name, value, context)
        print(f"{description} ({value}): {result['significance']} - {result['clinical_pearl']}")
    
    print()

def test_tsh_logic():
    """Test TSH evaluation logic"""
    engine = ClinicalSignificanceEngine()
    
    print("=== TSH Tests ===")
    
    test_cases = [
        ("Normal TSH", "tsh", 2.5, {}),
        ("Borderline low", "tsh", 0.3, {}),
        ("Borderline high", "tsh", 5.2, {}),
        ("Suppressed", "tsh", 0.05, {}),
        ("Hypothyroid", "tsh", 15.0, {}),
    ]
    
    for description, test_name, value, context in test_cases:
        result = engine.evaluate_lab_value(test_name, value, context)
        print(f"{description} ({value}): {result['significance']} - {result['clinical_pearl']}")
    
    print()

def test_alias_recognition():
    """Test lab test alias recognition"""
    engine = ClinicalSignificanceEngine()
    
    print("=== Alias Recognition Tests ===")
    
    aliases = [
        ("hgb", 12.5),
        ("hb", 12.5),
        ("k", 4.0),
        ("k+", 4.0),
        ("cr", 1.0),
        ("creat", 1.0),
        ("gluc", 100),
        ("bg", 100),
    ]
    
    for alias, value in aliases:
        result = engine.evaluate_lab_value(alias, value, {})
        if 'error' not in result:
            print(f"✓ {alias} → {result['test_name']}")
        else:
            print(f"✗ {alias} → ERROR: {result['error']}")
    
    print()

def test_significance_distribution():
    """Test the distribution of significance levels across various values"""
    engine = ClinicalSignificanceEngine()
    
    print("=== Significance Level Distribution ===")
    
    # Test hemoglobin for female across a range
    hgb_values = [6.0, 9.5, 11.7, 12.0, 13.5, 15.0, 19.0]
    context = {"sex": "female", "age": 30}
    
    print("Hemoglobin (Female, 30y):")
    for value in hgb_values:
        result = engine.evaluate_lab_value("hemoglobin", value, context)
        level = result.get('level', 0)
        sig = result.get('significance', 'unknown')
        print(f"  {value} g/dL → Level {level} ({sig})")
    
    print()

if __name__ == "__main__":
    print("Clinical Significance Engine Test Suite")
    print("=" * 50)
    
    test_hemoglobin_logic()
    test_potassium_logic()
    test_glucose_logic()
    test_creatinine_logic()
    test_tsh_logic()
    test_alias_recognition()
    test_significance_distribution()
    
    print("Test suite completed!") 