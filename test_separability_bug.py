import sys
sys.path.insert(0, 'repos/astropy_astropy__astropy-12907')

from astropy.modeling import models as m
from astropy.modeling.separable import separability_matrix

# Test case 1: Simple compound model
print("Test 1: Simple compound model")
cm = m.Linear1D(10) & m.Linear1D(5)
print(f"cm = m.Linear1D(10) & m.Linear1D(5)")
print(f"separability_matrix(cm) =")
print(separability_matrix(cm))
print()

# Test case 2: Complex model without nesting
print("Test 2: Complex model without nesting")
model2 = m.Pix2Sky_TAN() & m.Linear1D(10) & m.Linear1D(5)
print(f"model2 = m.Pix2Sky_TAN() & m.Linear1D(10) & m.Linear1D(5)")
print(f"separability_matrix(model2) =")
print(separability_matrix(model2))
print()

# Test case 3: Nested compound model (the bug)
print("Test 3: Nested compound model (the bug)")
model3 = m.Pix2Sky_TAN() & cm
print(f"model3 = m.Pix2Sky_TAN() & cm")
print(f"separability_matrix(model3) =")
print(separability_matrix(model3))
print()

# Expected result for comparison
print("Expected for Test 3 (should be same as Test 2):")
print("array([[ True,  True, False, False],")
print("       [ True,  True, False, False],")
print("       [False, False,  True, False],")
print("       [False, False, False,  True]])")