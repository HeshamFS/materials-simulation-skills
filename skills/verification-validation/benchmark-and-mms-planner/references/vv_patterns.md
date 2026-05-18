# Verification And Validation Patterns

Use MMS to test implementation correctness, especially source terms, boundary conditions, Jacobians, and time integration. Use canonical benchmarks to test physical behavior against known solutions or community references.

Recommended evidence ladder:

1. Unit-level operator checks.
2. MMS with observed order.
3. Canonical benchmark.
4. Problem-specific conservation or balance laws.
5. Uncertainty propagation for input parameters.

Avoid claiming validation from convergence alone. Convergence shows the code approaches some solution; it does not show that the model is physically correct.
