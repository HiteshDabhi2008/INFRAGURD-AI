# Member 4: Time Overrun Model Definition
# =========================================
# This document is generated as part of the Day-2 pipeline.
# See docs/member4_time_model.md for the full written documentation.

# Target: time_overrun_flag (binary: 1 if revised_completion_date > original_completion_date)
# Prediction Point: Implementation-time early warning (current monthly snapshot)
# Leakage Exclusions: revised_completion_date, time_overrun_months, revised_duration_days
