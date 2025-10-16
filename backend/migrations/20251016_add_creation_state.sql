-- Add creation_state column to projects for flow persistence
-- Migration: 20251016_add_creation_state

ALTER TABLE projects 
ADD COLUMN creation_state JSON NULL;

-- Add comment
COMMENT ON COLUMN projects.creation_state IS 'Stores project creation flow state for persistence across refreshes';
