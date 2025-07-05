# MB
![Build Status](https://github.com/0xfbravo/mb/actions/workflows/ci.yaml/badge.svg)
[![codecov](https://codecov.io/gh/0xfbravo/mb/graph/badge.svg?token=L19xK9ugij)](https://codecov.io/gh/0xfbravo/mb)

![Python](https://img.shields.io/badge/Python_3.12-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0056B3?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Clean Architecture](https://img.shields.io/badge/Clean%20Architecture-000000?style=for-the-badge&logo=cleanarchitecture&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

Welcome to the MB project which is a sample project written in Python with FastAPI!

This project was created to demonstrate my knowledge of Python, FastAPI, and Clean Architecture.

This document will help you understand the project structure and get started quickly.

## 🚀 Quick Start (TL;DR)

```bash
# First time setup
make setup

# Copy .env.example to .env and edit it with your configuration
cp .env.example .env

# Start the application environment with Docker Compose
make up/build/dev
```

Open a new browser tab and navigate to http://localhost:8000/docs or http://localhost:8000/redoc to see the API documentation.

## 🏗️ Project Structure

```
.
├── app/                    # Source code directory
│   ├── data/               # Data layer
│   ├── domain/             # Domain layer
│   ├── presentation/       # Presentation layer
│   ├── utils/              # Utility functions
│   └── main.py             # Application entry point
├── test/                   # Test files
│   ├── integration/        # Integration tests
│   ├── unit/               # Unit tests
│   └── conftest.py         # Test configuration file
├── .dockerignore           # Docker ignore file
├── .env.example            # Environment variables example to be copied as .env locally
├── Dockerfile              # Dockerfile for building the Docker image
├── main.py                 # Application entry point
├── Makefile                # Makefile with multiple useful commands
├── README.md               # This file
├── requirements-dev.in     # Development dependencies input file for pip-tools
├── requirements-dev.txt    # Development dependencies output file for pip-tools
├── requirements.in         # Production dependencies input file for pip-tools
└── requirements.txt        # Production dependencies output file for pip-tools
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or later
- pip3 (Python package installer)
- Docker and Docker Compose
- Make (for using Makefile commands)

### 🛠️ Setup

1. Clone the repository:
```bash
git clone git@github.com:0xfbravo/mb.git
cd mb
```

2. Set up the development environment:
```bash
make setup
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Install the package in development mode:
```bash
make install
```

5. Run the development server:
```bash
make run
```

## 🏗️ Architecture

The project follows Clean Architecture principles with clear separation of concerns:

### Layers

1. **API Layer** (`app/presentation/api/`)
   - Implements REST API endpoints
   - Handles request/response transformation
   - Calls domain layers to perform business logic

2. **Service Layer** (`app/domain/services/`)
   - Contains business logic and rules
   - Implements use cases
   - Independent of external frameworks

3. **Repository Layer** (`app/data/repositories/`)
   - Implements data access interfaces
   - Handles external dependencies
   - Database, cache, and external service integrations

4. **Domain Layer** (`app/domain/models/`)
   - Defines data models and entities
   - Contains domain-specific logic
   - Independent of infrastructure concerns

## 🗄️ Database Configuration

The application uses PostgreSQL with Tortoise ORM for database operations and connection pooling.

### Connection Pool Configuration

The database connection pool is managed by Tortoise ORM and can be configured using environment variables:

```bash
# Database connection settings
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Connection pool settings (optional)
DB_POOL_MIN_SIZE=1          # Minimum number of connections in the pool
DB_POOL_MAX_SIZE=10         # Maximum number of connections in the pool
DB_POOL_MAX_IDLE=300        # Maximum time (seconds) a connection can be idle
DB_POOL_TIMEOUT=30          # Timeout (seconds) for getting a connection from the pool
```

### Pool Statistics

You can monitor the connection pool performance using the `get_pool_stats()` method:

```python
from app.data.database import DatabaseManager

# Get pool statistics
stats = await db_manager.get_pool_stats()
print(f"Pool size: {stats['pool_size']}")
print(f"Checked out connections: {stats['checked_out']}")
print(f"Available connections: {stats['checked_in']}")
```

## 🧪 Testing

Run all tests:
```bash
make test
```

Run unit tests only:
```bash
make test/unit
```

Run integration tests:
```bash
make test/integration
```

Run tests with coverage:
```bash
make test/all
```

Generate coverage report:
```bash
make coverage
```

## 🏭 Development Workflow

1. **Creating a New Feature**
   - Create a new branch from `main`
   - Follow the domain-driven structure
   - Add tests for new functionality
   - Submit a pull request

2. **Code Style**
   - Follow PEP 8 guidelines
   - Use `black` and `isort` for code formatting
   - Use `flake8` and `mypy` for code quality

3. **Documentation**
   - Document all public APIs
   - Update README when adding new features
   - Add docstrings for functions and classes

## 🔧 Available Make Commands

```bash
make setup           # Setup development environment (venv, tools, dependencies)
make build          # Build the Python package
make install        # Install the package in development mode
make clean          # Clean build artifacts and cache files
make test           # Run all tests (unit and integration)
make test/unit      # Run unit tests only
make test/integration # Run integration tests
make test/all       # Run all tests with coverage
make coverage       # Generate test coverage report
make lint           # Run linter (flake8 and mypy)
make fmt            # Format code with black and isort
make deps           # Install dependencies
make deps/update    # Update dependencies
make deps/compile   # Compile requirements files
make security       # Run security checks
make run            # Run the application
make run/dev        # Run with auto-reload
make mocks          # Mock generation info
make docker-build   # Build Docker image (requires SERVICE=<service_name>)
```

Note: For `docker-build`, you need to specify the service name:
```bash
make docker-build SERVICE=<service_name>
```

## 📦 Dependency Management

### Production Dependencies
Add production dependencies to `requirements.txt`:
```bash
pip3 install package_name
pip3 freeze > requirements.txt
```

### Development Dependencies
Add development dependencies to `requirements-dev.txt`:
```bash
pip3 install package_name
pip3 freeze > requirements-dev.txt
```

### Using pip-tools (Recommended)
For better dependency management, use `pip-tools`:
```bash
make deps/compile
```

## 📚 Key Concepts

### Service Implementation
Each service follows this pattern:
```python
class ServiceImpl:
    def __init__(self, repository: Repository, logger: Logger):
        self.repository = repository
        self.logger = logger
    
    def execute(self, request: Request) -> Response:
        # Business logic here
        pass
```

### Error Handling
- Use custom exception classes
- Handle errors at appropriate layers
- Return meaningful error messages

### Logging
- Use structured logging
- Include relevant context in logs
- Log at appropriate levels

## 🧪 Testing Strategy

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Focus on business logic

### Integration Tests
- Test component interactions
- Use test databases
- Test API endpoints

### Test Coverage
- Aim for >80% coverage
- Focus on critical business logic
- Use `pytest-cov` for coverage reporting

## 🔒 Security

Run security checks:
```bash
make security
```

This will:
- Check for known vulnerabilities in dependencies
- Scan for security issues in your code
- Provide recommendations for fixes

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Set up the development environment (`make setup`)
4. Make your changes
5. Run tests (`make test`)
6. Format your code (`make fmt`)
7. Run linting (`make lint`)
8. Commit your changes (`git commit -m 'Add some amazing feature'`)
9. Push to the branch (`git push origin feature/amazing-feature`)
10. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue if needed

## 🔄 CI/CD

The project uses GitHub Actions for:
- Running tests
- Linting and formatting checks
- Security scanning
- Building Docker images
- Deploying to environments

## 🎯 Best Practices

1. **Code Organization**
   - Keep files focused and small
   - Use meaningful names
   - Follow Python idioms and PEP 8

2. **Testing**
   - Write unit tests for business logic
   - Include integration tests
   - Maintain good test coverage

3. **Documentation**
   - Keep documentation up to date
   - Document complex algorithms
   - Include examples in docstrings

4. **Dependencies**
   - Pin dependency versions
   - Use virtual environments
   - Regularly update dependencies

5. **Code Quality**
   - Use type hints
   - Follow linting rules
   - Format code consistently