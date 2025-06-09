# KeePass MCP Server Testing Guide

This comprehensive guide covers all aspects of testing your KeePass MCP Server.

## 🚀 Quick Start

```bash
# 1. Setup test environment
chmod +x test_setup.sh run_tests.sh
./test_setup.sh

# 2. Run all tests
./run_tests.sh all

# 3. Test manually
python manual_test.py --interactive
```

## 📋 Test Types Available

### 1. **Automated Test Suite**

#### **Unit Tests**
```bash
# Run all unit tests
./run_tests.sh unit

# Run specific component tests
./run_tests.sh test_entry_operations.py
./run_tests.sh test_search_functionality.py
./run_tests.sh test_security.py
```

#### **Integration Tests**
```bash
# Test complete workflows
./run_tests.sh integration

# Quick integration test
pytest tests/test_integration.py::TestKeePassMCPServerIntegration::test_authentication_workflow -v
```

#### **Performance Tests**
```bash
# Test performance and concurrency
./run_tests.sh performance
```

#### **Code Quality**
```bash
# Linting, formatting, type checking
./run_tests.sh quality
```

### 2. **Manual Testing**

#### **Interactive Mode**
```bash
# Interactive testing interface
python manual_test.py --interactive

# Available commands in interactive mode:
# auth      - Test authentication
# search    - Test search functionality  
# entry     - Test entry operations
# group     - Test group operations
# password  - Test password operations
# database  - Test database operations
# all       - Run all tests
```

#### **Specific Test Categories**
```bash
# Test specific functionality
python manual_test.py --test auth
python manual_test.py --test search
python manual_test.py --test entry
```

### 3. **Integration with Claude Desktop**

#### **Setup Claude Desktop Testing**
1. Copy test configuration:
```bash
cp tests/claude_test_config.json ~/.config/Claude/claude_desktop_config.json
```

2. Start the MCP server:
```bash
python -m keepass_mcp_server
```

3. Test with Claude:
```
"Please unlock my KeePass database with password TestPassword123!"
"Search for GitHub credentials"
"Create a new entry for test.com with username testuser"
```

## 🗂️ Test Data

### **Test Database Details**
- **Location**: `tests/data/test_database.kdbx`
- **Password**: `TestPassword123!`
- **Contains**:
  - Development group (GitHub, GitLab entries)
  - Personal group (Email, Social Media entries) 
  - Work group (Company Portal entry)

### **Test Credentials**
```
GitHub Account:
  Username: developer
  Password: SecurePassword123!
  URL: https://github.com

Email Account:
  Username: john.doe@email.com
  Password: EmailPass789!
  URL: https://mail.google.com

Social Media (weak password):
  Username: johndoe
  Password: WeakPass
  URL: https://twitter.com
```

## 🧪 Testing Scenarios

### **Authentication Testing**
```bash
# Test successful authentication
python -c "
import asyncio
from manual_test import ManualTester
tester = ManualTester()
tester.setup_test_environment()
asyncio.run(tester.test_authentication())
"

# Test wrong password
export KEEPASS_DB_PATH=tests/data/test_database.kdbx
python -m keepass_mcp_server
# Then try with wrong password in Claude
```

### **Search Testing**
```bash
# Test various search patterns
python manual_test.py --test search

# Or in interactive mode:
python manual_test.py -i
> search
```

### **CRUD Operations Testing**
```bash
# Test create, read, update, delete
python manual_test.py --test entry

# Test group operations
python manual_test.py --test group
```

### **Security Testing**
```bash
# Test weak passwords
pytest tests/test_security.py::test_weak_password_detection -v

# Test session management
pytest tests/test_security.py::test_session_timeout -v
```

### **Performance Testing**
```bash
# Test large datasets
pytest tests/test_integration.py::TestPerformanceAndConcurrency::test_large_result_set_handling -v

# Test concurrent operations
pytest tests/test_integration.py::TestPerformanceAndConcurrency::test_concurrent_search_operations -v
```

## 🔧 Development Testing

### **Test-Driven Development**
```bash
# Run tests in watch mode
pytest tests/ --maxfail=1 --tb=short -q

# Run specific test while developing
pytest tests/test_entry_operations.py::test_create_entry -v --tb=long
```

### **Debug Mode Testing**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python manual_test.py --test auth

# Or run server with debug
export LOG_LEVEL=DEBUG
python -m keepass_mcp_server
```

### **Coverage Testing**
```bash
# Generate coverage report
pytest --cov=keepass_mcp_server --cov-report=html tests/

# View coverage
open htmlcov/index.html
```

## 🐛 Troubleshooting Tests

### **Common Issues**

#### **PyKeePass Not Available**
```bash
pip install pykeepass>=4.0.0
```

#### **Test Database Missing**
```bash
# Recreate test database
./test_setup.sh
```

#### **Permission Errors**
```bash
chmod +x test_setup.sh run_tests.sh
chmod 644 tests/data/test_database.kdbx
```

#### **MCP Import Errors**
```bash
pip install mcp>=1.0.0
```

### **Test Debugging**
```bash
# Run with verbose output
pytest tests/test_integration.py -v -s --tb=long

# Run single test with debugging
pytest tests/test_entry_operations.py::test_create_entry -v -s --pdb

# Check logs
tail -f tests/logs/test.log
```

## 📊 Test Results

### **Expected Test Coverage**
- **Entry Operations**: 95%+
- **Group Operations**: 90%+  
- **Search Functionality**: 95%+
- **Security Features**: 90%+
- **Backup System**: 85%+
- **Overall**: 90%+

### **Performance Benchmarks**
- **Authentication**: < 500ms
- **Search (100 entries)**: < 100ms
- **Entry Creation**: < 200ms
- **Database Save**: < 1s

## 🎯 Test Strategy

### **For New Features**
1. Write unit tests first
2. Add integration tests
3. Test manually
4. Update documentation

### **For Bug Fixes**
1. Create failing test that reproduces bug
2. Fix the bug
3. Ensure test passes
4. Add regression test

### **Before Release**
1. Run complete test suite: `./run_tests.sh all`
2. Test with real KeePass database
3. Test Claude Desktop integration
4. Performance testing
5. Security audit

## 🔄 Continuous Testing

### **Pre-commit Testing**
```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit checks
pre-commit run --all-files
```

### **GitHub Actions**
The project includes CI/CD workflows that run:
- Unit tests on multiple Python versions
- Integration tests
- Code quality checks
- Security scans

## 📝 Test Reports

### **Generate Reports**
```bash
# HTML coverage report
./run_tests.sh all

# JUnit XML for CI
pytest --junitxml=test-results.xml tests/

# Performance report
pytest --benchmark-only --benchmark-sort=mean tests/
```

### **View Reports**
- **Coverage**: `htmlcov/index.html`
- **Test Results**: Terminal output or CI dashboard
- **Logs**: `tests/logs/test.log`

---

**Happy Testing! 🧪✨**

Remember: Good tests are your safety net - they give you confidence to refactor, add features, and deploy with peace of mind.
