-- Migration: add_shelves_table
-- Creates a `shelves` table to track bookshelf/shelf structure independently of
-- book inventory, enabling empty shelves and shelf reordering.

CREATE TABLE IF NOT EXISTS shelves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bookshelf TEXT NOT NULL,
    shelf_number INTEGER NOT NULL,
    position_order INTEGER NOT NULL,
    UNIQUE(bookshelf, shelf_number)
);

-- Seed from existing inventory data so all current shelves are registered.
INSERT OR IGNORE INTO shelves (bookshelf, shelf_number, position_order)
SELECT shelf_bookshelf, shelf_shelf, shelf_shelf
FROM inv
WHERE shelf_bookshelf IS NOT NULL AND shelf_shelf IS NOT NULL
GROUP BY shelf_bookshelf, shelf_shelf
ORDER BY shelf_bookshelf, shelf_shelf;
