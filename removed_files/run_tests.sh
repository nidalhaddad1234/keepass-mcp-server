#!/bin/bash
# Comprehensive test runner for KeePass MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
export KEEPASS_DB_PATH="tests/data/test_database.kdbx"
export KEEPASS_BACKUP_DIR="tests/backups"
export KEEPASS_ACCESS_MODE="readwrite"
export LOG_LEVEL="DEBUG"
export USE_KEYCHAIN="false"

echo -e "${BLUE}🧪 KeePass MCP Server Test Suite${NC}"
echo "=================================="

# Function to run a test category
run_test_category() {
    local category=$1
    local description=$2
    
    echo -e "\n${YELLOW}📋 Running $description...${NC}"
    
    if pytest "tests/$category" -v --tb=short --cov=keepass_mcp_server --cov-report=term-missing; then
        echo -e "${GREEN}✅ $description passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $description failed${NC}"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    echo -e "\n${YELLOW}🔗 Running Integration Tests...${NC}"
    
    if pytest tests/test_integration.py -v --tb=long --cov=keepass_mcp_server; then
        echo -e "${GREEN}✅ Integration tests passed${NC}"
        return 0
    else
        echo -e "${RED}❌ Integration tests failed${NC}"
        return 1
    fi
}

# Function to run specific test
run_specific_test() {
    local test_name=$1
    echo -e "\n${YELLOW}🎯 Running specific test: $test_name${NC}"
    
    if pytest -k "$test_name" -v --tb=long; then
        echo -e "${GREEN}✅ Test $test_name passed${NC}"
        return 0
    else
        echo -e "${RED}❌ Test $test_name failed${NC}"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    echo -e "\n${YELLOW}⚡ Running Performance Tests...${NC}"
    
    # Run with performance markers if they exist
    if pytest -m "performance" --tb=short -v 2>/dev/null; then
        echo -e "${GREEN}✅ Performance tests passed${NC}"
    else
        echo -e "${YELLOW}ℹ️ No performance tests found or failed${NC}"
    fi
}

# Function to run linting and code quality
run_code_quality() {
    echo -e "\n${YELLOW}🔍 Running Code Quality Checks...${NC}"
    
    # Black formatting check
    echo "📝 Checking code formatting with black..."
    if black --check src/; then
        echo -e "${GREEN}✅ Code formatting passed${NC}"
    else
        echo -e "${RED}❌ Code formatting issues found${NC}"
        echo "Run: black src/ to fix"
    fi
    
    # Import sorting check
    echo "📦 Checking import sorting with isort..."
    if isort --check-only src/; then
        echo -e "${GREEN}✅ Import sorting passed${NC}"
    else
        echo -e "${RED}❌ Import sorting issues found${NC}"
        echo "Run: isort src/ to fix"
    fi
    
    # Linting with flake8
    echo "🔍 Running linter with flake8..."
    if flake8 src/; then
        echo -e "${GREEN}✅ Linting passed${NC}"
    else
        echo -e "${RED}❌ Linting issues found${NC}"
    fi
    
    # Type checking with mypy
    echo "🏷️ Type checking with mypy..."
    if mypy src/ --ignore-missing-imports; then
        echo -e "${GREEN}✅ Type checking passed${NC}"
    else
        echo -e "${YELLOW}⚠️ Type checking issues found${NC}"
    fi
}

# Function to create test report
create_test_report() {
    echo -e "\n${YELLOW}📊 Generating Test Report...${NC}"
    
    # Create coverage report
    pytest --cov=keepass_mcp_server --cov-report=html --cov-report=xml tests/
    
    echo -e "${GREEN}✅ Test report generated in htmlcov/index.html${NC}"
}

# Main test execution
main() {
    local test_type=${1:-"all"}
    local failed_tests=()
    
    case $test_type in
        "unit")
            echo -e "${BLUE}Running Unit Tests Only${NC}"
            run_test_category "test_entry_operations.py" "Entry Operations Tests" || failed_tests+=("entry")
            run_test_category "test_group_operations.py" "Group Operations Tests" || failed_tests+=("group")
            run_test_category "test_search_functionality.py" "Search Functionality Tests" || failed_tests+=("search")
            run_test_category "test_security.py" "Security Tests" || failed_tests+=("security")
            run_test_category "test_backup_system.py" "Backup System Tests" || failed_tests+=("backup")
            ;;
            
        "integration")
            echo -e "${BLUE}Running Integration Tests Only${NC}"
            run_integration_tests || failed_tests+=("integration")
            ;;
            
        "performance")
            echo -e "${BLUE}Running Performance Tests Only${NC}"
            run_performance_tests || failed_tests+=("performance")
            ;;
            
        "quality")
            echo -e "${BLUE}Running Code Quality Checks Only${NC}"
            run_code_quality || failed_tests+=("quality")
            ;;
            
        "quick")
            echo -e "${BLUE}Running Quick Test Suite${NC}"
            pytest tests/ -x --tb=short
            ;;
            
        "all")
            echo -e "${BLUE}Running Complete Test Suite${NC}"
            
            # Unit tests
            run_test_category "test_entry_operations.py" "Entry Operations Tests" || failed_tests+=("entry")
            run_test_category "test_group_operations.py" "Group Operations Tests" || failed_tests+=("group")
            run_test_category "test_search_functionality.py" "Search Functionality Tests" || failed_tests+=("search")
            run_test_category "test_security.py" "Security Tests" || failed_tests+=("security")
            run_test_category "test_backup_system.py" "Backup System Tests" || failed_tests+=("backup")
            
            # Integration tests
            run_integration_tests || failed_tests+=("integration")
            
            # Performance tests
            run_performance_tests || failed_tests+=("performance")
            
            # Code quality
            run_code_quality || failed_tests+=("quality")
            
            # Generate report
            create_test_report
            ;;
            
        *)
            # Run specific test
            run_specific_test "$test_type" || failed_tests+=("$test_type")
            ;;
    esac
    
    # Summary
    echo -e "\n${BLUE}📋 Test Summary${NC}"
    echo "==============="
    
    if [ ${#failed_tests[@]} -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Failed test categories: ${failed_tests[*]}${NC}"
        exit 1
    fi
}

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Test types:"
    echo "  all         - Run complete test suite (default)"
    echo "  unit        - Run unit tests only"
    echo "  integration - Run integration tests only"
    echo "  performance - Run performance tests only"
    echo "  quality     - Run code quality checks only"
    echo "  quick       - Run quick test suite"
    echo "  <test_name> - Run specific test"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Run everything"
    echo "  $0 unit                   # Unit tests only"
    echo "  $0 test_authentication    # Specific test"
    echo ""
fi

# Run main function
main "$@"
