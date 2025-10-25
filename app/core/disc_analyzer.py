import json
from .database_manager import DatabaseManager

def recalculate_disc_profile(case_id: int):
    """
    Fetches all inputs for a case, applies the fusion algorithm, and saves a new evaluation.
    """
    db = DatabaseManager.get_instance()
    
    # 1. Obtener todos los inputs y las ponderaciones
    inputs = db.get_inputs_for_case(case_id)
    weights = {
        'text': float(db.get_setting('weight_text')),
        'html': float(db.get_setting('weight_html')),
        'image': float(db.get_setting('weight_image'))
    }
    
    valid_inputs = []
    for inp in inputs:
        if inp['gemini_raw_response']:
            try:
                data = json.loads(inp['gemini_raw_response'])
                if 'disc_vector' in data and all(k in data['disc_vector'] for k in ['d', 'i', 's', 'c']):
                    valid_inputs.append({
                        'type': inp['input_type'],
                        'data': data
                    })
            except json.JSONDecodeError:
                print(f"Skipping input {inp['id']} due to invalid JSON.")
    
    if not valid_inputs:
        print("No valid inputs with Gemini analysis found to calculate a profile.")
        return

    # 2. Aplicar el algoritmo de promedio ponderado
    total_weight = 0
    final_vector = {'d': 0, 'i': 0, 's': 0, 'c': 0}
    
    for inp in valid_inputs:
        weight = weights.get(inp['type'], 0.1) # Default weight if not found
        total_weight += weight
        for key in final_vector:
            final_vector[key] += inp['data']['disc_vector'][key] * weight

    if total_weight > 0:
        for key in final_vector:
            final_vector[key] /= total_weight
            
    # Normalizar para que la suma sea 100
    current_sum = sum(final_vector.values())
    if current_sum > 0:
        factor = 100 / current_sum
        for key in final_vector:
            final_vector[key] *= factor

    # 3. Calcular confianza y justificación
    # Para PoC, la confianza es simple: aumenta con más evidencia.
    confidence = min(100, 20 * len(valid_inputs)) 
    justification = "\n\n---\n\n".join([inp['data']['analysis'] for inp in valid_inputs])

    # 4. Guardar la nueva evaluación
    latest_version = db.get_latest_evaluation_version(case_id)
    new_version = latest_version + 1
    
    db.create_disc_evaluation(
        case_id=case_id,
        version=new_version,
        d=final_vector['d'],
        i=final_vector['i'],
        s=final_vector['s'],
        c=final_vector['c'],
        confidence=confidence,
        justification=justification
    )
    print(f"Successfully created DISC Evaluation v{new_version} for case {case_id}.")
