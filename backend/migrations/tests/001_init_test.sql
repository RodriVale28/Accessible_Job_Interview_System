-- Tests for 001_init.sql. Run on an empty database after 001.

CREATE FUNCTION expect_fail(stmt TEXT) RETURNS void AS $$
BEGIN
  EXECUTE stmt;
  RAISE EXCEPTION 'expected failure but succeeded: %', stmt USING ERRCODE = 'P0001';
EXCEPTION WHEN OTHERS THEN
  IF SQLSTATE = 'P0001' THEN RAISE; END IF;
END $$ LANGUAGE plpgsql;

INSERT INTO question_library (category, difficulty, prompt, expected_keywords) VALUES
  ('Data Structures', 'Easy', 'What is a stack?', '{lifo,push,pop}'),
  ('Algorithms', 'Easy', 'Explain binary search.', '{sorted,middle}');
INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions)
  VALUES ('00000000-0000-0000-0000-00000000000a', 'Junior Developer', 'Easy', 15, 5);
INSERT INTO session_questions (session_id, question_id, q_index) VALUES (1, 1, 1);
INSERT INTO responses (session_id, question_id, answer_text) VALUES (1, 1, 'push and pop');
INSERT INTO responses (session_id, question_id, is_blank) VALUES (1, 2, true);
INSERT INTO feedback (session_id, question_id, response_id, score, correct) VALUES (1, 1, 1, 80, true);

-- question_library
SELECT expect_fail($q$INSERT INTO question_library (category, difficulty, prompt, expected_keywords) VALUES ('X', 'Expert', 'p1', '{a}')$q$);
SELECT expect_fail($q$INSERT INTO question_library (category, difficulty, prompt, expected_keywords) VALUES ('X', 'Easy', 'p2', '{}')$q$);
SELECT expect_fail($q$INSERT INTO question_library (category, difficulty, prompt, expected_keywords) VALUES ('X', 'Easy', 'What is a stack?', '{a}')$q$);

-- sessions
SELECT expect_fail($q$INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions) VALUES (gen_random_uuid(), 'Dev', 'Easy', 20, 5)$q$);
SELECT expect_fail($q$INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions) VALUES (gen_random_uuid(), 'D', 'Easy', 15, 5)$q$);
SELECT expect_fail($q$INSERT INTO sessions (user_id, job_title, interview_type, difficulty, duration_min, total_questions) VALUES (gen_random_uuid(), 'Dev', 'Trivia', 'Easy', 15, 5)$q$);
SELECT expect_fail($q$UPDATE sessions SET status = 'completed' WHERE id = 1$q$);
SELECT expect_fail($q$UPDATE sessions SET completed_at = now() WHERE id = 1$q$);
SELECT expect_fail($q$UPDATE sessions SET overall_score = 101 WHERE id = 1$q$);

-- session_questions
SELECT expect_fail($q$INSERT INTO session_questions (session_id, question_id, q_index) VALUES (1, 2, 0)$q$);
SELECT expect_fail($q$INSERT INTO session_questions (session_id, question_id, q_index) VALUES (1, 2, 1)$q$);
SELECT expect_fail($q$INSERT INTO session_questions (session_id, question_id, q_index) VALUES (1, 1, 2)$q$);

-- responses and feedback
SELECT expect_fail($q$INSERT INTO responses (session_id, question_id, answer_text) VALUES (1, 1, 'again')$q$);
SELECT expect_fail($q$INSERT INTO feedback (session_id, question_id, score, correct) VALUES (1, 2, 101, false)$q$);

-- Completing a session works; deleting it cascades
UPDATE sessions SET status = 'completed', completed_at = now(), overall_score = 80 WHERE id = 1;
DELETE FROM sessions WHERE id = 1;
DO $$ BEGIN
  IF (SELECT count(*) FROM session_questions) + (SELECT count(*) FROM responses) + (SELECT count(*) FROM feedback) <> 0
  THEN RAISE EXCEPTION 'cascade delete failed'; END IF;
  IF (SELECT count(*) FROM question_library) <> 2 THEN RAISE EXCEPTION 'library rows lost'; END IF;
END $$;

SELECT 'ALL TESTS PASSED' AS result;
