-- S2-1.1: practice attempts and settings belong to real Supabase users.
-- Run in the Supabase SQL editor after 003.
-- Supabase only (auth.users does not exist in a plain local Postgres); local runs and CI skip it.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'practice_attempts_user_id_fkey') THEN
        ALTER TABLE practice_attempts ADD CONSTRAINT practice_attempts_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'user_settings_user_id_fkey') THEN
        ALTER TABLE user_settings ADD CONSTRAINT user_settings_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;
