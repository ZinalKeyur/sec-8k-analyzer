#!/bin/bash
# remove_cron.sh — removes the SEC 8-K analyzer cron job

crontab -l 2>/dev/null | grep -v "sec-8k-analyzer" | crontab -
echo "✅ Cron job removed."
