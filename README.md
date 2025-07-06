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

## 🌐 EVM Configuration

This application is configured to work with any EVM compatible blockchain.

By default, the application is configured to work with the `TEST` network.

So if you want to use, for example, the `ETHEREUM_SEPOLIA` network, you need to change the `selected` network in the `config.yaml` file to `ETHEREUM_SEPOLIA`.

Also you can configure the assets and networks in the `config.yaml` file, you just need to add the asset and network you want to use.

```yaml
assets:
  USDT:
    native: false
    ETHEREUM: "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ARBITRUM: "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
    BASE: "0xfde4c96c8593536e31f229ea8f37b2ada2699bb2" # Bridged USDT
    # ETHEREUM_SEPOLIA: "0x0000000000000000000000000000000000000000" # Unable to find official contract address
    # ARBITRUM_SEPOLIA: "0x0000000000000000000000000000000000000000" # Unable to find official contract address
    # BASE_SEPOLIA: "0x0000000000000000000000000000000000000000" # Unable to find official contract address
```

## 🏗️ Architecture

The project follows Clean Architecture principles with clear separation of concerns:

### Layers

1. **Presentation** (`app/presentation`)
   - Implements REST API endpoints (e.g. `app/presentation/api/`)
   - Handles request/response transformation
   - Calls domain layers to perform business logic
   - Can interact with user's input and output in multiple ways (e.g. CLI, HTTP, etc.)

2. **Data** (`app/data/`)
   - Handles external dependencies like database, cache, and external service integrations (e.g. `app/data/evm/`)
   - Implements data access interfaces

3. **Domain** (`app/domain/`)
   - Defines data models and entities split into sub-folders (e.g. `app/domain/wallet/`)
   - Contains domain-specific logic
   - Independent of infrastructure concerns, exclusively responsible for business logic

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