# Modern sese-engine Refactoring Standards

## Code Style

### Naming Conventions
- **Variables and functions**: `snake_case` in English
- **Classes**: `PascalCase` in English  
- **Constants**: `UPPER_SNAKE_CASE`
- **File names**: `snake_case.py`

### Type Hints
- All functions must have type hints
- Use `Optional[T]` for nullable values
- Use `List[T]`, `Dict[K, V]`, etc. for collections

### Documentation
- All modules need docstrings
- All public functions need docstrings
- Use Google-style docstrings

## Architecture Standards

### Project Structure
```
sese_engine/
├── src/
│   ├── crawler/          # Web crawler
│   ├── indexer/          # Index management
│   ├── search/           # Search engine
│   ├── storage/          # Data storage
│   ├── api/              # FastAPI endpoints
│   └── utils/            # Utility functions
├── tests/                # Unit tests
├── config/               # Configuration
└── docs/                 # Documentation
```

### Dependencies
- Use `pyproject.toml` for modern Python packaging
- Pin exact versions for reproducibility
- Use `poetry` or `pip-tools` for dependency management

## Error Handling
- Use custom exceptions
- Log all errors appropriately
- Provide meaningful error messages
- Use HTTP status codes appropriately in API

## Testing
- Minimum 80% test coverage
- Use `pytest` for testing
- Mock external dependencies
- Test both happy and error paths

## Security
- Input validation for all user inputs
- Sanitize outputs
- Use environment variables for secrets
- Implement rate limiting

## Performance
- Use async/await for I/O operations
- Implement caching strategies
- Monitor performance metrics
- Use connection pooling