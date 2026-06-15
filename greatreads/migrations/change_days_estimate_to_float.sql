-- Change days_estimate from INTEGER to REAL (Float) to support fractional days
-- This allows for more precise progress tracking

-- SQLite doesn't support ALTER COLUMN TYPE directly, so we need to:
-- 1. Create a new column
-- 2. Copy data
-- 3. Drop old column
-- 4. Rename new column

ALTER TABLE read ADD COLUMN days_estimate_new REAL;
UPDATE read SET days_estimate_new = days_estimate;
ALTER TABLE read DROP COLUMN days_estimate;
ALTER TABLE read RENAME COLUMN days_estimate_new TO days_estimate;

