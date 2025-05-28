from flask import Flask, Blueprint, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime
import re
import logging
import time

# Configure logging for debugging network issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint
app = Blueprint('lab_value_helper', __name__, 
                template_folder='templates',
                static_folder='static')

# Add CORS and error handling middleware
@app.after_request
def after_request(response):
    """Add CORS headers and ensure proper connection handling"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Cache-Control')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', '0')
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler for better debugging"""
    logger.error(f"Application error: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'An internal error occurred. Please try again.',
        'details': str(error) if app.debug else None
    }), 500

class ClinicalSignificanceEngine:
    """Core engine for determining clinical significance of lab values"""
    
    SIGNIFICANCE_LEVELS = {
        'normal': {'level': 1, 'color': 'text-gray-600', 'bg': '', 'label': 'Normal'},
        'likely_insignificant': {'level': 2, 'color': 'text-gray-500', 'bg': 'bg-gray-50', 'label': 'Likely Insignificant'},
        'possibly_significant': {'level': 3, 'color': 'text-amber-700', 'bg': 'bg-amber-50', 'label': 'Possibly Significant'},
        'clinically_significant': {'level': 4, 'color': 'text-orange-700', 'bg': 'bg-orange-50', 'label': 'Clinically Significant'},
        'critical': {'level': 5, 'color': 'text-red-700', 'bg': 'bg-red-50', 'label': 'Critical'}
    }
    
    def __init__(self):
        self.lab_tests = self._init_lab_tests()
    
    def _init_lab_tests(self):
        """Initialize lab test definitions with clinical logic"""
        return {
            'hemoglobin': {
                'name': 'Hemoglobin',
                'aliases': ['hgb', 'hb', 'hemoglobin', 'haemoglobin'],
                'unit': 'g/dL',
                'reference_range': 'M: 13.5-17.5, F: 12.0-15.5',
                'logic': self._evaluate_hemoglobin
            },
            'creatinine': {
                'name': 'Creatinine',
                'aliases': ['cr', 'creat', 'creatinine'],
                'unit': 'mg/dL',
                'reference_range': 'M: 0.7-1.3, F: 0.6-1.1',
                'logic': self._evaluate_creatinine
            },
            'potassium': {
                'name': 'Potassium',
                'aliases': ['k', 'k+', 'potassium'],
                'unit': 'mEq/L',
                'reference_range': '3.5-5.0',
                'logic': self._evaluate_potassium
            },
            'glucose': {
                'name': 'Glucose',
                'aliases': ['gluc', 'glucose', 'bg', 'blood glucose'],
                'unit': 'mg/dL',
                'reference_range': 'Fasting: 70-99, Random: <140',
                'logic': self._evaluate_glucose
            },
            'tsh': {
                'name': 'TSH',
                'aliases': ['tsh', 'thyroid stimulating hormone'],
                'unit': 'mIU/L',
                'reference_range': '0.4-4.0',
                'logic': self._evaluate_tsh
            }
        }
    
    def find_test(self, test_name):
        """Find lab test by name or alias"""
        test_name_lower = test_name.lower().strip()
        for test_key, test_info in self.lab_tests.items():
            if test_name_lower in test_info['aliases']:
                return test_key, test_info
        return None, None
    
    def evaluate_lab_value(self, test_name, value, patient_context=None):
        """Main evaluation function"""
        if patient_context is None:
            patient_context = {}
            
        test_key, test_info = self.find_test(test_name)
        if not test_info:
            return {
                'error': f'Lab test "{test_name}" not recognized',
                'suggestions': list(self.lab_tests.keys())
            }
        
        try:
            value = float(value)
        except ValueError:
            return {'error': 'Invalid numeric value'}
        
        result = test_info['logic'](value, patient_context)
        result.update({
            'test_name': test_info['name'],
            'value': value,
            'unit': test_info['unit'],
            'reference_range': test_info['reference_range'],
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def _evaluate_hemoglobin(self, value, context):
        """Hemoglobin evaluation with sex and age considerations"""
        sex = context.get('sex', 'unknown').lower()
        age = context.get('age', 30)
        
        # Critical values
        if value < 7.0:
            return {
                'significance': 'critical',
                'clinical_pearl': 'Severe anemia - transfusion may be needed',
                'action': 'Immediate evaluation required'
            }
        
        if value > 18.0:
            return {
                'significance': 'critical',
                'clinical_pearl': 'Severe polycythemia - check for hyperviscosity',
                'action': 'Immediate evaluation required'
            }
        
        # Sex-specific evaluation
        if sex == 'female':
            if 11.5 <= value <= 11.9:
                return {
                    'significance': 'likely_insignificant',
                    'clinical_pearl': 'Mild anemia - common in menstruating women',
                    'action': 'Consider iron studies if symptoms present'
                }
            elif 10.0 <= value < 11.5:
                return {
                    'significance': 'possibly_significant',
                    'clinical_pearl': 'Moderate anemia - investigate cause',
                    'action': 'Iron studies, B12/folate recommended'
                }
            elif value < 10.0:
                return {
                    'significance': 'clinically_significant',
                    'clinical_pearl': 'Significant anemia requiring evaluation',
                    'action': 'Comprehensive anemia workup needed'
                }
            elif value >= 12.0:
                return {
                    'significance': 'normal',
                    'clinical_pearl': 'Normal hemoglobin for female',
                    'action': 'No action needed'
                }
        
        elif sex == 'male':
            if 13.0 <= value <= 13.4:
                return {
                    'significance': 'possibly_significant',
                    'clinical_pearl': 'Borderline low for male - monitor trend',
                    'action': 'Consider repeat if symptomatic'
                }
            elif value < 13.0:
                return {
                    'significance': 'clinically_significant',
                    'clinical_pearl': 'Anemia in male - needs investigation',
                    'action': 'Comprehensive anemia workup recommended'
                }
            elif value >= 13.5:
                return {
                    'significance': 'normal',
                    'clinical_pearl': 'Normal hemoglobin for male',
                    'action': 'No action needed'
                }
        
        # Default for unknown sex
        if 12.0 <= value <= 16.0:
            return {
                'significance': 'normal',
                'clinical_pearl': 'Within normal range',
                'action': 'No action needed'
            }
        else:
            return {
                'significance': 'possibly_significant',
                'clinical_pearl': 'Abnormal value - consider clinical context',
                'action': 'Clinical correlation recommended'
            }
    
    def _evaluate_potassium(self, value, context):
        """Potassium evaluation with tight critical ranges"""
        if value < 2.5 or value >= 6.0:
            action = 'Immediate action required - cardiac monitoring'
            if value < 2.5:
                pearl = 'Severe hypokalemia - arrhythmia risk'
            else:
                pearl = 'Severe hyperkalemia - arrhythmia risk'
            return {
                'significance': 'critical',
                'clinical_pearl': pearl,
                'action': action
            }
        
        if value < 3.0 or value > 5.5:
            return {
                'significance': 'clinically_significant',
                'clinical_pearl': 'Significant electrolyte imbalance',
                'action': 'Correction needed, monitor closely'
            }
        
        if (3.0 <= value <= 3.4) or (5.1 <= value <= 5.5):
            return {
                'significance': 'possibly_significant',
                'clinical_pearl': 'Mild imbalance - recheck if hemolyzed sample suspected',
                'action': 'Consider repeat, monitor trend'
            }
        
        return {
            'significance': 'normal',
            'clinical_pearl': 'Normal potassium level',
            'action': 'No action needed'
        }
    
    def _evaluate_creatinine(self, value, context):
        """Creatinine evaluation with age adjustments"""
        age = context.get('age', 30)
        sex = context.get('sex', 'unknown').lower()
        
        # Age-adjusted normal ranges
        if sex == 'female':
            normal_upper = 1.1 if age < 65 else 1.3
            if value <= normal_upper:
                return {
                    'significance': 'normal',
                    'clinical_pearl': 'Normal kidney function',
                    'action': 'No action needed'
                }
        elif sex == 'male':
            normal_upper = 1.3 if age < 65 else 1.5
            if value <= normal_upper:
                return {
                    'significance': 'normal',
                    'clinical_pearl': 'Normal kidney function',
                    'action': 'No action needed'
                }
        
        if value > 4.0:
            return {
                'significance': 'critical',
                'clinical_pearl': 'Severe kidney dysfunction',
                'action': 'Urgent nephrology consultation'
            }
        
        if value > 2.0:
            return {
                'significance': 'clinically_significant',
                'clinical_pearl': 'Significant kidney impairment',
                'action': 'Nephrology evaluation recommended'
            }
        
        return {
            'significance': 'possibly_significant',
            'clinical_pearl': 'Mild elevation - monitor trend',
            'action': 'Repeat in 1-2 weeks, check trend'
        }
    
    def _evaluate_glucose(self, value, context):
        """Glucose evaluation considering fasting status"""
        fasting = context.get('fasting', False)
        
        if value > 400:
            return {
                'significance': 'critical',
                'clinical_pearl': 'Severe hyperglycemia - DKA risk',
                'action': 'Immediate evaluation for DKA/HHS'
            }
        
        if value < 50:
            return {
                'significance': 'critical',
                'clinical_pearl': 'Severe hypoglycemia',
                'action': 'Immediate treatment required'
            }
        
        if fasting:
            if value >= 126:
                return {
                    'significance': 'clinically_significant',
                    'clinical_pearl': 'Diabetes diagnostic threshold',
                    'action': 'Diabetes workup recommended'
                }
            elif 100 <= value <= 109:
                return {
                    'significance': 'possibly_significant',
                    'clinical_pearl': 'Impaired fasting glucose - prediabetes range',
                    'action': 'Lifestyle counseling, monitor trend, consider HbA1c'
                }
            elif value >= 110:
                return {
                    'significance': 'possibly_significant',
                    'clinical_pearl': 'Impaired fasting glucose - upper prediabetes range',
                    'action': 'Lifestyle counseling, monitor trend, consider HbA1c'
                }
        else:
            if value >= 200:
                return {
                    'significance': 'clinically_significant',
                    'clinical_pearl': 'Random glucose suggests diabetes',
                    'action': 'Fasting glucose or HbA1c needed'
                }
        
        return {
            'significance': 'normal',
            'clinical_pearl': 'Normal glucose level',
            'action': 'No action needed'
        }
    
    def _evaluate_tsh(self, value, context):
        """TSH evaluation with wide normal variation"""
        if value > 10.0:
            return {
                'significance': 'clinically_significant',
                'clinical_pearl': 'Overt hypothyroidism',
                'action': 'Thyroid hormone replacement needed'
            }
        
        if value < 0.1:
            return {
                'significance': 'clinically_significant',
                'clinical_pearl': 'Suppressed TSH - hyperthyroidism',
                'action': 'Free T4, T3 recommended'
            }
        
        if value > 4.5 or value < 0.4:
            return {
                'significance': 'possibly_significant',
                'clinical_pearl': 'Borderline thyroid function',
                'action': 'Consider repeat in 6-8 weeks'
            }
        
        return {
            'significance': 'normal',
            'clinical_pearl': 'Normal thyroid function',
            'action': 'No action needed'
        }

# Initialize the engine
engine = ClinicalSignificanceEngine()

@app.route('/')
def index():
    """Main lab value helper interface"""
    return render_template('lab_helper_index.html')

@app.route('/evaluate', methods=['POST', 'OPTIONS'])
def evaluate_lab():
    """API endpoint for lab value evaluation"""
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = jsonify({'status': 'ok'})
        return response
        
    request_id = f"req_{int(time.time() * 1000)}"
    logger.info(f"[{request_id}] Starting single lab evaluation")
    
    try:
        # Validate request content type
        if not request.is_json:
            logger.warning(f"[{request_id}] Invalid content type: {request.content_type}")
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            logger.warning(f"[{request_id}] Empty request body")
            return jsonify({'error': 'Request body is required'}), 400
        
        test_name = data.get('test_name', '').strip()
        value = data.get('value', '')
        patient_context = data.get('patient_context', {})
        
        logger.info(f"[{request_id}] Evaluating: {test_name} = {value}")
        
        if not test_name or not value:
            logger.warning(f"[{request_id}] Missing required fields")
            return jsonify({'error': 'Test name and value are required'}), 400
        
        # Validate value is numeric
        try:
            float(value)
        except (ValueError, TypeError):
            logger.warning(f"[{request_id}] Invalid value format: {value}")
            return jsonify({'error': 'Value must be a valid number'}), 400
        
        result = engine.evaluate_lab_value(test_name, value, patient_context)
        
        if 'error' in result:
            logger.warning(f"[{request_id}] Evaluation error: {result['error']}")
            return jsonify(result), 400
        
        # Add styling information
        significance_info = engine.SIGNIFICANCE_LEVELS[result['significance']]
        result.update(significance_info)
        
        logger.info(f"[{request_id}] Evaluation completed successfully: {result['significance']}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'An error occurred while processing your request',
            'request_id': request_id
        }), 500

@app.route('/bulk_evaluate', methods=['POST', 'OPTIONS'])
def bulk_evaluate():
    """Evaluate multiple lab values at once"""
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = jsonify({'status': 'ok'})
        return response
        
    request_id = f"bulk_{int(time.time() * 1000)}"
    logger.info(f"[{request_id}] Starting bulk lab evaluation")
    
    try:
        # Validate request content type
        if not request.is_json:
            logger.warning(f"[{request_id}] Invalid content type: {request.content_type}")
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            logger.warning(f"[{request_id}] Empty request body")
            return jsonify({'error': 'Request body is required'}), 400
        
        lab_values = data.get('lab_values', [])
        patient_context = data.get('patient_context', {})
        
        if not lab_values:
            logger.warning(f"[{request_id}] No lab values provided")
            return jsonify({'error': 'Lab values are required'}), 400
        
        if len(lab_values) > 50:  # Reasonable limit
            logger.warning(f"[{request_id}] Too many lab values: {len(lab_values)}")
            return jsonify({'error': 'Maximum 50 lab values allowed per request'}), 400
        
        logger.info(f"[{request_id}] Processing {len(lab_values)} lab values")
        
        results = []
        
        for i, lab in enumerate(lab_values):
            try:
                test_name = lab.get('test_name', '').strip()
                value = lab.get('value', '')
                
                if not test_name or not value:
                    logger.warning(f"[{request_id}] Lab {i}: Missing test_name or value")
                    results.append({'error': f'Lab {i+1}: Missing test name or value'})
                    continue
                
                # Validate value is numeric
                try:
                    float(value)
                except (ValueError, TypeError):
                    logger.warning(f"[{request_id}] Lab {i}: Invalid value format: {value}")
                    results.append({'error': f'Lab {i+1}: Invalid value format'})
                    continue
                
                result = engine.evaluate_lab_value(test_name, value, patient_context)
                
                if 'error' not in result:
                    significance_info = engine.SIGNIFICANCE_LEVELS[result['significance']]
                    result.update(significance_info)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"[{request_id}] Error processing lab {i}: {str(e)}")
                results.append({'error': f'Lab {i+1}: Processing error'})
        
        # Calculate detailed summary with all significance levels
        critical_count = len([r for r in results if r.get('significance') == 'critical'])
        clinically_significant_count = len([r for r in results if r.get('significance') == 'clinically_significant'])
        possibly_significant_count = len([r for r in results if r.get('significance') == 'possibly_significant'])
        likely_insignificant_count = len([r for r in results if r.get('significance') == 'likely_insignificant'])
        normal_count = len([r for r in results if r.get('significance') == 'normal'])
        
        # "Need attention" includes all non-normal categories
        need_attention_count = critical_count + clinically_significant_count + possibly_significant_count + likely_insignificant_count
        
        summary = {
            'total_tests': len(results),
            'need_attention_count': need_attention_count,
            'normal_count': normal_count,
            'critical_count': critical_count,
            'clinically_significant_count': clinically_significant_count,
            'possibly_significant_count': possibly_significant_count,
            'likely_insignificant_count': likely_insignificant_count,
            'message': f"{need_attention_count} findings need review, {normal_count} within normal limits"
        }
        
        logger.info(f"[{request_id}] Bulk evaluation completed: {summary}")
        
        return jsonify({
            'results': results,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'An error occurred while processing your request',
            'request_id': request_id
        }), 500

@app.route('/tests')
def available_tests():
    """Return available lab tests and their aliases"""
    tests_info = {}
    for key, info in engine.lab_tests.items():
        tests_info[key] = {
            'name': info['name'],
            'aliases': info['aliases'],
            'unit': info['unit']
        }
    return jsonify(tests_info)

if __name__ == '__main__':
    app.run(debug=True) 