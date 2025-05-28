# Lab Value Helper - Clinical Significance Engine

A clinical lab value interpreter that **REDUCES alert fatigue** by showing what matters. Built with Flask and a sophisticated 5-tier clinical significance system.

## Key Innovation: Clinical Significance Levels

Instead of simple abnormal flags, we use a nuanced 5-tier system:

1. **🟢 Normal** - No flag, reduces visual noise
2. **🔘 Likely Insignificant** - Gray, acknowledges but de-emphasizes
3. **🟡 Possibly Significant** - Amber, warrants consideration  
4. **🟠 Clinically Significant** - Orange, action recommended
5. **🔴 Critical** - Red, immediate action required

## Features

### Core Functionality
- **Smart Lab Recognition**: Accepts common abbreviations (K, Hgb, Cr, etc.)
- **Context-Aware Assessment**: Considers patient age, sex, fasting status
- **Clinical Pearls**: Brief explanations for significance decisions
- **Actionable Guidance**: Specific next steps for each result

### Supported Lab Tests
- **Hemoglobin**: Sex-specific ranges, considers menstruation
- **Creatinine**: Age-adjusted expectations
- **Potassium**: Tight critical ranges for cardiac safety
- **Glucose**: Fasting vs random logic
- **TSH**: Wide normal variation recognition

### UI/UX Features
- **Quiet Interface**: Normal values have no visual markers
- **Summary Dashboard**: "2 findings need review, 8 within normal"
- **Filter Toggles**: "Show All" vs "Actionable Only"
- **Bulk Input**: Paste entire lab panels
- **Mobile-Optimized**: Touch-friendly for bedside use

## Clinical Logic Examples

### Hemoglobin
- Female 11.5-11.9 g/dL → **Likely Insignificant** - "Common in menstruating women"
- Male 13.0-13.4 g/dL → **Possibly Significant** - "Borderline low for male"
- Anyone <7.0 g/dL → **Critical** - "Severe anemia - transfusion may be needed"

### Potassium
- 3.3-3.4 or 5.1-5.2 mEq/L → **Possibly Significant** - "Recheck if hemolyzed"
- <2.5 or >6.0 mEq/L → **Critical** - "Arrhythmia risk - cardiac monitoring"

## Usage

### Single Lab Entry
1. Enter patient context (age, sex, fasting status)
2. Input test name and value
3. Get immediate clinical significance assessment

### Bulk Lab Panel
```
Hemoglobin: 11.8
Potassium: 3.3
Creatinine: 1.1
Glucose: 105
```

### API Endpoints
- `POST /evaluate` - Single lab evaluation
- `POST /bulk_evaluate` - Multiple lab evaluation
- `GET /tests` - Available test information

## Architecture

### Clinical Significance Engine
- Modular evaluation logic for each lab test
- Context-aware thresholds
- Evidence-based clinical decision rules

### Flask Blueprint Structure
- Clean separation from main app
- RESTful API design
- Responsive web interface

## Success Metric

A physician should look at 20 lab results and immediately know which 2-3 actually need their attention, with confidence that nothing critical is hidden in the "normal" results.

## Future Enhancements

- Pattern recognition (concerning combinations)
- Trend analysis (increasing/decreasing)
- Additional lab tests (CBC, CMP, LFTs)
- Pediatric ranges
- Medication interaction flags 