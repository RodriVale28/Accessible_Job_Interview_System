-- S1-0.1 Login: sessions belong to real Supabase users.
-- Run once in the Supabase SQL editor after the login PR is merged.
-- Supabase only (auth.users does not exist in a plain local Postgres); local runs and CI skip it.
-- If guest sessions are still in the table this fails without changing anything:
-- remove those rows first.

ALTER TABLE sessions
    ADD CONSTRAINT sessions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
