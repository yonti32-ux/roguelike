# How the Testing Infrastructure Works

This document explains how the pytest testing infrastructure works in this codebase.

## Table of Contents

1. [Overview](#overview)
2. [How Pytest Discovers Tests](#how-pytest-discovers-tests)
3. [How Fixtures Work](#how-fixtures-work)
4. [Writing Tests](#writing-tests)
5. [Running Tests](#running-tests)
6. [Example Walkthrough](#example-walkthrough)
7. [Common Patterns](#common-patterns)

---

## Overview

The testing infrastructure uses **pytest**, a Python testing framework. Here's the basic flow:

1. **You write test functions** that check if code works correctly
2. **Pytest automatically finds** all test files
3. **Pytest runs the tests** and reports results
4. **Fixtures provide** reusable setup code

---

## How Pytest Discovers Tests

Pytest automatically finds tests based on naming conventions defined in `pytest.ini`:

```ini
python_files = test_*.py      # Files starting with "test_"
python_classes = Test*        # Classes starting with "Test"
python_functions = test_*     # Functions starting with "test_"
```

### Example Structure

```
tests/
├── unit/
│   └── test_systems/
│       └── test_statuses.py    ← Pytest finds this (starts with "test_")
│           └── class TestStatusEffect:    ← Pytest finds this (starts with "Test")
│               └── def test_status_effect_creation():  ← Pytest runs this (starts with "test_")
```

When you run `pytest`, it:
1. Scans the `tests/` directory (configured in `pytest.ini`)
2. Finds all files matching `test_*.py`
3. Finds all classes matching `Test*`
4. Finds all functions matching `test_*`
5. Runs each test function

---

## How Fixtures Work

**Fixtures** are reusable setup functions that prepare test data. They're defined in `tests/conftest.py` and automatically available to all test files.

### Example Fixture

```python
@pytest.fixture
def sample_inventory():
    """Create a sample inventory for testing."""
    from systems.inventory import Inventory
    return Inventory()
```

### Using Fixtures

To use a fixture, just add it as a parameter to your test function:

```python
def test_add_item(sample_inventory):  # ← fixture injected here
    """Test adding items to inventory."""
    sample_inventory.add_item("sword")
    assert "sword" in sample_inventory.items
```

**How it works:**
1. Pytest sees the `sample_inventory` parameter
2. It looks for a fixture with that name in `conftest.py`
3. It calls the fixture function to create the object
4. It passes the result to your test function

### Fixture Scopes

Fixtures can have different scopes (how long they live):

- **`function`** (default): Created fresh for each test
- **`class`**: Created once per test class
- **`module`**: Created once per test file
- **`session`**: Created once for all tests

**Example:**
```python
@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    """Initialize pygame once for all tests."""
    pygame.init()
    yield  # Tests run here
    pygame.quit()  # Cleanup after all tests
```

The `autouse=True` means it runs automatically, even if you don't request it.

---

## Writing Tests

### Basic Test Structure

Tests follow the **Arrange-Act-Assert** pattern:

```python
def test_something():
    # Arrange: Set up the test data
    status = StatusEffect(name="Poison", duration=3)
    
    # Act: Do the thing you're testing
    status.duration -= 1
    
    # Assert: Check the result
    assert status.duration == 2
```

### Test Classes

Group related tests in classes:

```python
class TestStatusEffect:
    """Tests for StatusEffect dataclass."""
    
    def test_status_effect_creation(self):
        """Test creating a status effect."""
        status = StatusEffect(name="Poison", duration=3)
        assert status.name == "Poison"
        assert status.duration == 3
    
    def test_status_effect_defaults(self):
        """Test status effect default values."""
        status = StatusEffect(name="Test")
        assert status.duration == 0
        assert status.stacks == 1
```

### Using Assertions

Pytest uses Python's `assert` statement:

```python
assert condition                    # Passes if condition is True
assert value == expected           # Check equality
assert value in collection         # Check membership
assert len(list) == 3              # Check length
assert obj.attribute == expected   # Check attribute
```

If an assertion fails, pytest shows:
- What value you got
- What value was expected
- The line where it failed

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output (shows each test name)
pytest -v

# Run a specific test file
pytest tests/unit/test_systems/test_statuses.py

# Run a specific test
pytest tests/unit/test_systems/test_statuses.py::TestStatusEffect::test_status_effect_creation

# Run tests matching a pattern
pytest -k "status"  # Runs all tests with "status" in the name
```

### With Coverage

```bash
# Run tests and show coverage
pytest --cov

# Generate HTML coverage report
pytest --cov
# Then open htmlcov/index.html in your browser
```

Coverage shows which lines of code were executed during tests. Higher coverage = more code is tested.

---

## Example Walkthrough

Let's walk through a real example from `tests/unit/test_systems/test_statuses.py`:

### The Code Being Tested

```python
# systems/statuses.py
def tick_statuses(statuses: List[StatusEffect]) -> int:
    """Advance all statuses by one turn. Returns total DOT damage."""
    total_dot = 0
    remaining: List[StatusEffect] = []
    
    for s in statuses:
        if s.flat_damage_each_turn:
            total_dot += s.flat_damage_each_turn * max(1, s.stacks)
        s.duration -= 1
        if s.duration > 0:
            remaining.append(s)
    
    statuses[:] = remaining  # Replace list in place
    return total_dot
```

### The Test

```python
def test_tick_statuses_applies_dot(self):
    """Test that damage over time is applied correctly."""
    # Arrange: Create status effects with damage over time
    statuses = [
        StatusEffect(
            name="Poison",
            duration=3,
            stacks=1,
            flat_damage_each_turn=5,  # 5 damage per turn
        ),
        StatusEffect(
            name="Burn",
            duration=2,
            stacks=2,
            flat_damage_each_turn=3,  # 3 damage per turn, 2 stacks
        ),
    ]
    
    # Act: Call the function we're testing
    damage = tick_statuses(statuses)
    
    # Assert: Check the results
    assert damage == 11  # 5 (Poison) + 6 (Burn: 3 * 2 stacks) = 11
    assert statuses[0].duration == 2  # Duration decremented from 3 to 2
    assert statuses[1].duration == 1  # Duration decremented from 2 to 1
```

### What Happens When You Run It

1. **Pytest finds the test**: `test_tick_statuses_applies_dot` matches `test_*`
2. **Pytest runs the test**:
   - Creates the status effects
   - Calls `tick_statuses(statuses)`
   - Checks the assertions
3. **If all assertions pass**: Test shows as `PASSED`
4. **If any assertion fails**: Test shows as `FAILED` with details

### Example Output

```
tests/unit/test_systems/test_statuses.py::TestTickStatuses::test_tick_statuses_applies_dot PASSED
```

Or if it fails:

```
FAILED tests/unit/test_systems/test_statuses.py::TestTickStatuses::test_tick_statuses_applies_dot
assert damage == 11
assert 10 == 11
```

---

## Common Patterns

### Testing with Fixtures

```python
def test_inventory_add_item(sample_inventory):
    """Use the sample_inventory fixture."""
    sample_inventory.add_item("sword")
    assert "sword" in sample_inventory.items
```

### Testing Exceptions

```python
def test_divide_by_zero():
    """Test that division by zero raises an error."""
    with pytest.raises(ZeroDivisionError):
        result = 1 / 0
```

### Testing Multiple Cases

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    """Test doubling with multiple inputs."""
    assert input * 2 == expected
```

### Testing Edge Cases

```python
def test_empty_list():
    """Test behavior with empty input."""
    statuses = []
    damage = tick_statuses(statuses)
    assert damage == 0
    assert len(statuses) == 0
```

### Isolating Tests

Each test should be independent:

```python
def test_one(sample_inventory):
    sample_inventory.add_item("sword")
    assert len(sample_inventory.items) == 1

def test_two(sample_inventory):
    # This gets a fresh inventory, not the one from test_one
    assert len(sample_inventory.items) == 0
```

---

## Key Concepts Summary

1. **Test Discovery**: Pytest finds files/classes/functions matching patterns
2. **Fixtures**: Reusable setup code (like `sample_inventory`)
3. **Assertions**: `assert` statements check if code works correctly
4. **Isolation**: Each test runs independently with fresh data
5. **Coverage**: Shows which code is tested

---

## Next Steps

1. **Run the existing tests**: `pytest` to see them in action
2. **Write a simple test**: Try testing a function you understand well
3. **Read the test files**: Look at `tests/unit/test_systems/test_statuses.py` for examples
4. **Add more tests**: Test systems you're working on

---

## Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Test Files**: See `tests/unit/` for examples
- **Fixtures**: See `tests/conftest.py` for available fixtures
- **Configuration**: See `pytest.ini` for pytest settings

