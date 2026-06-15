-- Add current_percent and current_percent_manual_override columns to read table
-- These columns track the user's actual progress through in-progress books

ALTER TABLE read ADD COLUMN current_percent REAL;
ALTER TABLE read ADD COLUMN current_percent_manual_override BOOLEAN DEFAULT 0;

