-- Tests for 002_rls_policies.sql (run on an empty test database after 001 and 002)
-- User A and user B each have one session; each must see only their own rows.

INSERT INTO auth.users (id) VALUES
  ('00000000-0000-0000-0000-00000000000a'),
  ('00000000-0000-0000-0000-00000000000b');

INSERT INTO question_library (category, difficulty, prompt, expected_keywords) VALUES
  ('Data Structures', 'Easy', 'What is a stack?', '{lifo,push,pop}');

INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions) VALUES
  ('00000000-0000-0000-0000-00000000000a', 'Junior Developer', 'Easy', 15, 1),
  ('00000000-0000-0000-0000-00000000000b', 'Data Analyst', 'Easy', 15, 1);

INSERT INTO session_questions (session_id, question_id, q_index) VALUES (1, 1, 1), (2, 1, 1);
INSERT INTO responses (session_question_id, answer_text) VALUES (1, 'A answer'), (2, 'B answer');
INSERT INTO feedback (session_question_id, score, is_correct) VALUES (1, 80, true), (2, 20, false);

CREATE FUNCTION expect_rows(label TEXT, stmt TEXT, expected INT) RETURNS void AS $$
DECLARE n INT;
BEGIN
  EXECUTE 'SELECT count(*) FROM (' || stmt || ') x' INTO n;
  IF n <> expected THEN RAISE EXCEPTION '%: expected % rows, got %', label, expected, n; END IF;
END $$ LANGUAGE plpgsql;

CREATE FUNCTION expect_fail(stmt TEXT) RETURNS void AS $$
BEGIN
  EXECUTE stmt;
  RAISE EXCEPTION 'expected failure but succeeded: %', stmt USING ERRCODE = 'P0001';
EXCEPTION WHEN OTHERS THEN
  IF SQLSTATE = 'P0001' THEN RAISE; END IF;
END $$ LANGUAGE plpgsql;

-- Logged in as user A
SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000a', false);
SELECT expect_rows('A sessions', $q$SELECT 1 FROM sessions WHERE job_title = 'Junior Developer'$q$, 1);
SELECT expect_rows('A sees no B session', $q$SELECT 1 FROM sessions WHERE job_title = 'Data Analyst'$q$, 0);
SELECT expect_rows('A session_questions', 'SELECT 1 FROM session_questions', 1);
SELECT expect_rows('A responses', $q$SELECT 1 FROM responses WHERE answer_text = 'A answer'$q$, 1);
SELECT expect_rows('A sees no B response', $q$SELECT 1 FROM responses WHERE answer_text = 'B answer'$q$, 0);
SELECT expect_rows('A feedback', 'SELECT 1 FROM feedback WHERE score = 80', 1);
SELECT expect_rows('A sees no B feedback', 'SELECT 1 FROM feedback WHERE score = 20', 0);
SELECT expect_rows('library is server-only', 'SELECT 1 FROM question_library', 0);
SELECT expect_fail($q$INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions) VALUES ('00000000-0000-0000-0000-00000000000a', 'x', 'Easy', 15, 1)$q$);
SELECT expect_fail($q$INSERT INTO feedback (session_question_id, score, is_correct) VALUES (1, 100, true)$q$);
UPDATE sessions SET job_title = 'hacked';
DELETE FROM responses;

-- Logged in as user B
SELECT set_config('request.jwt.claim.sub', '00000000-0000-0000-0000-00000000000b', false);
SELECT expect_rows('B sessions', $q$SELECT 1 FROM sessions WHERE job_title = 'Data Analyst'$q$, 1);
SELECT expect_rows('B sees no A session', $q$SELECT 1 FROM sessions WHERE job_title = 'Junior Developer'$q$, 0);
SELECT expect_rows('B responses', 'SELECT 1 FROM responses', 1);

-- Not logged in
RESET ROLE;
SET ROLE anon;
SELECT expect_rows('anon sessions', 'SELECT 1 FROM sessions', 0);
SELECT expect_rows('anon responses', 'SELECT 1 FROM responses', 0);
RESET ROLE;

-- The blocked update and delete above changed nothing
SELECT expect_rows('no rows hacked', $q$SELECT 1 FROM sessions WHERE job_title = 'hacked'$q$, 0);
SELECT expect_rows('responses intact', 'SELECT 1 FROM responses', 2);

SELECT 'ALL TESTS PASSED' AS result;
