import re

# regex patterns
patterns = {
    "quadratic_equation": r"([-+]?\d*)x\^2(\s*([-+]\s*\d*)x)*\s*([-+]\s*\d*)\s*=\s*0",
    "middle_term_split": r"([-+]?\d*)x\^2(\s*([-+]\s*\d*)x)*\s*([-+]\s*\d*)\s*",
    "factoring_common_terms":r"([-+]?\d*)x\s*\(\s*(x\s*[-+]\s*\d*)\s*\)\s*(\s*[-+]?\s*\d*\s*)\(\s*(x\s*[-+]\s*\d*)\s*\)",
    "final_factorization": r"\((x[-+]\d*)\)\((x[-+]\d*)\)",
    "solution": r"x\s*=\s*([-+]?\d+)"
}

# Test input
steps = [
    "x^2 + 8x + 2 = 0",
    "x^2 + 2x + x + 2 ",
    "x^2 + x + 2x + 2 ",
    "x(x+2) + 1(x+2) = 0",
    "(x+1)(x+2) = 0",
    "x = -1",
    "x = -2"
]

# Function to classify steps
def classify_step(step):
    for label, pattern in patterns.items():
        if re.search(pattern, step):
            return label
    return "unknown" # if this is the case the step is sent to ocr again

# Run classification
classified_steps = {step: classify_step(step) for step in steps}

# Output classification
for step, category in classified_steps.items():
    print(f"{step} → {category}")
