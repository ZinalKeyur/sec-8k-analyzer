#!/bin/bash
# setup_cron.sh
# =============
# Sets up a daily cron job to run the 8-K analyzer every morning at 8:00 AM.
# Run once with:  bash setup_cron.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(which python3)"
LOG_FILE="$SCRIPT_DIR/output/cron.log"

CRON_JOB="0 8 * * 1-5 cd $SCRIPT_DIR && $PYTHON main.py >> $LOG_FILE 2>&1"

echo "================================================"
echo "  SEC 8-K Analyzer — Cron Setup"
echo "================================================"
echo ""
echo "  Script dir : $SCRIPT_DIR"
echo "  Python     : $PYTHON"
echo "  Schedule   : Every weekday at 8:00 AM"
echo "  Log file   : $LOG_FILE"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "sec-8k-analyzer"; then
    echo "  ⚠️  A cron job for sec-8k-analyzer already exists."
    echo "  Remove it first with:  bash remove_cron.sh"
    exit 1
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "  ✅ Cron job added successfully!"
echo ""
echo "  The analyzer will run automatically every weekday at 8:00 AM."
echo "  Reports will be saved to: $SCRIPT_DIR/output/"
echo ""
echo "  To check your cron jobs:    crontab -l"
echo "  To remove this cron job:    bash remove_cron.sh"
echo "  To run manually right now:  python3 main.py"
echo "================================================"
