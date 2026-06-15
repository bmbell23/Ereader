-- Add 3-coordinate bookshelf location system to inv table.
--
-- shelf_bookshelf : The physical bookshelf label (e.g. "A", "B")
-- shelf_shelf     : The shelf number on that bookshelf (e.g. 1, 2, 3)
-- shelf_position  : The position of the book on that shelf (1-based, left to right)
--
-- Migration from old 2-coordinate "location" column (e.g. "A1"):
--   shelf_bookshelf = first character of location
--   shelf_shelf     = numeric suffix of location
--   shelf_position  = sequential order within each bookshelf+shelf group

ALTER TABLE inv ADD COLUMN shelf_bookshelf VARCHAR;
ALTER TABLE inv ADD COLUMN shelf_shelf INTEGER;
ALTER TABLE inv ADD COLUMN shelf_position INTEGER;

-- Populate from existing location values (format: letter + digits, e.g. "A1", "B12")
UPDATE inv
SET
    shelf_bookshelf = UPPER(SUBSTR(location, 1, 1)),
    shelf_shelf     = CAST(SUBSTR(location, 2) AS INTEGER)
WHERE location IS NOT NULL AND location != '' AND TYPEOF(CAST(SUBSTR(location, 2) AS INTEGER)) = 'integer';

-- Assign sequential shelf_position within each (shelf_bookshelf, shelf_shelf) group
-- using row ordering by id (arbitrary initial order; user will reorder via drag-and-drop)
UPDATE inv
SET shelf_position = (
    SELECT COUNT(*)
    FROM inv AS i2
    WHERE i2.shelf_bookshelf = inv.shelf_bookshelf
      AND i2.shelf_shelf = inv.shelf_shelf
      AND i2.id <= inv.id
)
WHERE shelf_bookshelf IS NOT NULL AND shelf_shelf IS NOT NULL;
