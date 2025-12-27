#!/bin/bash

# Directory containing the plotting scripts
SCRIPT_DIR="./scripts"

echo "=== Reproducing all Python scripts under $SCRIPT_DIR ==="

# Enter scripts directory
cd "$SCRIPT_DIR" || {
    echo "Error: Cannot cd to $SCRIPT_DIR"
    exit 1
}

# Run every Python script
for script in *.py; do
    echo "----------------------------------------"
    echo "📄 Running: $script"
    echo "----------------------------------------"

    python3 "$script" 2>&1 | tee /tmp/pam_reproduce_log.txt
    STATUS=${PIPESTATUS[0]}

    # Surface lines mentioning saved outputs
    grep -iE 'saving to|saved at|\.pdf' /tmp/pam_reproduce_log.txt | sed 's/^/💾 /'

    if [ $STATUS -eq 0 ]; then
        echo "✅ $script ran successfully"
    else
        echo "❌ $script failed with exit code $STATUS"
    fi
done

echo "=== Done running all scripts ==="

