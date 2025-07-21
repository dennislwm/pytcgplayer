#!/bin/bash

check_env() {
    local errors=0

    # Check for required environment variables
    local required_env_vars=(
        # No environment variables required
    )

    echo "Checking environment variables..."
    for var in "${required_env_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            echo "ERROR: Environment variable $var is not set"
            errors=$((errors + 1))
        else
            echo "✓ $var is set"
        fi
    done

    # Check for required CLI applications
    local required_cli_apps=(
        "gh"
        "python"
        "pipenv"
        "shellcheck"
    )

    echo -e "\nChecking CLI applications..."
    for app in "${required_cli_apps[@]}"; do
        if ! command -v "$app" &> /dev/null; then
            echo "ERROR: CLI application '$app' is not installed or not in PATH"
            errors=$((errors + 1))
        else
            echo "✓ $app is available"
        fi
    done

    # Return status
    if [[ $errors -eq 0 ]]; then
        echo -e "\n✅ All environment checks passed"
        return 0
    else
        echo -e "\n❌ $errors error(s) found"
        return 1
    fi
}

# Allow script to be sourced or executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    check_env "$@"
fi