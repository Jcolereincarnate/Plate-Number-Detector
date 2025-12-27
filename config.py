PLATE_PATTERNS = {
    'standard': r'^[A-Z]{3}-?\d{3}[A-Z]{2}$', 
    'government': r'^[A-Z]{2}-?\d{2,4}-?[A-Z]{2}$',  
    'police': r'^(POL|NPF)-?\d{4,5}[A-Z]?$', 
    'military': r'^(NA|NAF|NN)-?\d{3,5}[A-Z]?$', 
    'diplomatic': r'^(CD|CMD|CC)-?\d{3,4}[A-Z]?$',
}