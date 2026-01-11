# Testing Guide

This directory contains the test suite for roguelike_v2.

## Structure

```
tests/
├── conftest.py          # Shared fixtures and pytest configuration
├── unit/                # Unit tests for individual systems
│   ├── test_systems/    # Tests for systems/ modules
│   └── test_engine/     # Tests for engine/ modules
└── integration/         # Integration tests (to be added)
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov
```

### Run specific test file
```bash
pytest tests/unit/test_systems/test_inventory.py
```

### Run specific test
```bash
pytest tests/unit/test_systems/test_inventory.py::TestInventory::test_add_item
```

### Run with verbose output
```bash
pytest -v
```

### Run only unit tests
```bash
pytest -m unit
```

## Test Organization

### Unit Tests (`tests/unit/`)

Unit tests focus on testing individual functions, classes, and modules in isolation.

- **test_systems/**: Tests for game logic systems (combat, inventory, perks, etc.)
- **test_engine/**: Tests for engine components (managers, controllers, etc.)

### Integration Tests (`tests/integration/`)

Integration tests verify that multiple systems work together correctly.

*To be added in future updates.*

## Writing Tests

### Example Test Structure

```python
"""
Unit tests for the example module.
"""

import pytest
from systems.example import ExampleClass


class TestExampleClass:
    """Tests for ExampleClass."""

    def test_initialization(self):
        """Test that ExampleClass initializes correctly."""
        obj = ExampleClass()
        assert obj.value == 0

    def test_method(self):
        """Test a specific method."""
        obj = ExampleClass()
        result = obj.do_something()
        assert result == expected_value
```

### Using Fixtures

Fixtures are defined in `conftest.py` and can be used in any test:

```python
def test_with_fixture(sample_inventory):
    """Test using the sample_inventory fixture."""
    assert len(sample_inventory.items) == 0
```

Available fixtures:
- `sample_screen`: Pygame surface for rendering tests
- `sample_inventory`: Empty Inventory instance
- `sample_stat_block`: Sample StatBlock
- `sample_hero_stats`: Sample HeroStats
- `sample_status_effects`: List of sample status effects
- `floor_manager`: FloorManager instance

## Test Coverage Goals

- **Core Systems**: > 80% coverage
  - Combat calculations
  - Inventory operations
  - Stat calculations
  - Status effects

- **Managers**: > 70% coverage
  - FloorManager
  - CameraManager
  - Other managers

- **Utilities**: > 60% coverage
  - Helper functions
  - Data loading

## Continuous Integration

*CI configuration to be added in the future.*

## Best Practices

1. **Test One Thing**: Each test should verify one specific behavior
2. **Descriptive Names**: Test names should clearly describe what they test
3. **Arrange-Act-Assert**: Structure tests with setup, action, and verification
4. **Use Fixtures**: Reuse common setup code via fixtures
5. **Isolation**: Tests should be independent and not rely on execution order
6. **Mock External Dependencies**: Use mocks for file I/O, pygame display, etc.

## Troubleshooting

### Pygame initialization errors

If you see pygame initialization errors, ensure you're using the fixtures from `conftest.py` which handle pygame setup/teardown.

### Import errors

Make sure you're running tests from the project root directory:
```bash
cd /path/to/roguelike_v2
pytest
```

### Coverage reports

HTML coverage reports are generated in `htmlcov/` directory:
```bash
# Generate report
pytest --cov

# Open report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Future Improvements

- [ ] Add integration tests for game flow
- [ ] Add performance/benchmark tests
- [ ] Add visual regression tests (if applicable)
- [ ] Set up CI/CD pipeline
- [ ] Add property-based testing (hypothesis)
- [ ] Add mutation testing

