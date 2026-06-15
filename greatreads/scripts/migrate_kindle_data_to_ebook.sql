-- Migration script to update "Kindle" to "Ebook" in all data
-- This updates all existing reading records and settings that reference Kindle

BEGIN TRANSACTION;

-- Update all Kindle readings to Ebook in the read table
UPDATE read
SET media = 'Ebook'
WHERE media = 'Kindle';

-- Update reading speeds in user_settings to use ebook_wpd instead of kindle_wpd
UPDATE user_settings
SET setting_value = REPLACE(setting_value, 'kindle_wpd', 'ebook_wpd')
WHERE setting_key = 'reading_speeds';

COMMIT;

