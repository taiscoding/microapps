"""
Utilities for the Radiology Translator application.
"""

# Common medical terms and their simplified explanations
COMMON_MEDICAL_TERMS = {
    "hypertension": "high blood pressure",
    "hyperlipidemia": "high cholesterol",
    "atherosclerosis": "hardening of the arteries",
    "cardiomegaly": "enlarged heart",
    "pneumonia": "lung infection",
    "pulmonary": "related to the lungs",
    "cardiac": "related to the heart",
    "hepatic": "related to the liver",
    "renal": "related to the kidneys",
    "cerebral": "related to the brain",
    "acute": "sudden or severe",
    "chronic": "long-lasting",
    "benign": "not cancerous",
    "malignant": "cancerous",
    "lesion": "area of abnormal tissue",
    "nodule": "small lump",
    "metastasis": "spread of cancer",
    "stenosis": "narrowing",
    "edema": "swelling due to fluid",
    "effusion": "fluid buildup",
    "ischemia": "restricted blood supply",
    "infarction": "tissue death due to lack of blood supply",
    "atrophy": "wasting away or decrease in size",
    "hypertrophy": "increase in size",
    "degenerative": "gradually deteriorating",
    "congenital": "present from birth",
    "idiopathic": "of unknown cause",
    "neoplasm": "abnormal growth or tumor",
    "bilateral": "on both sides",
    "unilateral": "on one side",
    "anterior": "front",
    "posterior": "back",
    "distal": "far from the center",
    "proximal": "near the center",
    "lateral": "to the side",
    "medial": "toward the middle",
    "ventral": "front side",
    "dorsal": "back side",
    "superior": "above",
    "inferior": "below",
    "aneurysm": "bulge in a blood vessel",
    "embolism": "blockage in a blood vessel",
    "thrombosis": "blood clot in a vessel",
    "hemorrhage": "bleeding",
    "contusion": "bruise",
    "fracture": "broken bone",
    "dislocation": "joint out of place",
    "sprain": "stretched or torn ligament",
    "strain": "stretched or torn muscle",
    "sclerosis": "hardening of tissue",
    "fibrosis": "thickening or scarring of tissue",
    "inflammation": "swelling and irritation",
    "calcification": "buildup of calcium",
    "opaque": "not allowing light to pass through",
    "lucent": "allowing light to pass through",
    "density": "degree of opacity or darkness",
    "radiolucent": "appears dark on X-ray",
    "radiopaque": "appears light on X-ray",
}


def identify_medical_terms(text):
    """
    Identifies medical terms in the given text.
    Returns a list of identified terms.
    """
    identified_terms = []
    for term in COMMON_MEDICAL_TERMS:
        if term.lower() in text.lower():
            identified_terms.append(term)
    
    return identified_terms


def get_simplified_explanation(term):
    """
    Returns a simplified explanation for a medical term.
    """
    return COMMON_MEDICAL_TERMS.get(term.lower(), "")


def enhance_translation_with_definitions(translation, medical_terms):
    """
    Adds definitions for medical terms in the translation.
    This is unused in the current version but could be used to enhance 
    the translation with tooltips or explanations for medical terms.
    """
    enhanced_translation = translation
    
    for term in medical_terms:
        if term.lower() in enhanced_translation.lower():
            explanation = get_simplified_explanation(term)
            if explanation:
                # Format term with its definition
                formatted_term = f"{term} ({explanation})"
                # Replace the term with the formatted version
                enhanced_translation = enhanced_translation.replace(term, formatted_term)
    
    return enhanced_translation 