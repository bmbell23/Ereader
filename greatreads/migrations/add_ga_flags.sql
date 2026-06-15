-- Add Graphic Audio tracking flags to inv table.
--
-- graphic_audio  : 1 when all/any linked ABS items are GA dramatizations
-- owned_in_library : 1 (default) when the GA book represents a genuinely
--                    owned title; 0 when the title matches another GR book
--                    but the author doesn't (suspicious auto-link → review
--                    queue).  Non-GA books always leave this at 1.

ALTER TABLE inv ADD COLUMN graphic_audio BOOLEAN DEFAULT 0;
ALTER TABLE inv ADD COLUMN owned_in_library BOOLEAN DEFAULT 1;
