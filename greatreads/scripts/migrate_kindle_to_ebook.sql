-- Migration script to rename owned_kindle to owned_ebook
-- This script renames the column in the inv table

-- SQLite doesn't support ALTER COLUMN RENAME directly, so we need to:
-- 1. Create a new table with the correct schema
-- 2. Copy data from old table to new table
-- 3. Drop old table
-- 4. Rename new table to old name

BEGIN TRANSACTION;

-- Create new table with correct schema
CREATE TABLE IF NOT EXISTS "inv_new" (
	id INTEGER NOT NULL, 
	book_id INTEGER NOT NULL, 
	owned_audio BOOLEAN, 
	owned_ebook BOOLEAN, 
	owned_physical BOOLEAN, 
	date_purchased DATE, 
	location VARCHAR, 
	read_status VARCHAR, 
	read_count INTEGER, 
	isbn_10 VARCHAR(10), 
	isbn_13 VARCHAR(13), 
	PRIMARY KEY (id), 
	FOREIGN KEY(book_id) REFERENCES books (id)
);

-- Copy data from old table to new table
INSERT INTO inv_new (id, book_id, owned_audio, owned_ebook, owned_physical, date_purchased, location, read_status, read_count, isbn_10, isbn_13)
SELECT id, book_id, owned_audio, owned_kindle, owned_physical, date_purchased, location, read_status, read_count, isbn_10, isbn_13
FROM inv;

-- Drop old table
DROP TABLE inv;

-- Rename new table to old name
ALTER TABLE inv_new RENAME TO inv;

COMMIT;

