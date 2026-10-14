-- Tests for 001_init.sql (run on an empty test database)

INSERT INTO auth.users (id) VALUES ('00000000-0000-0000-0000-000000000001');

INSERT INTO question_library (category, difficulty, prompt, expected_keywords) VALUES
  ('Data Structures', 'Easy', 'What is a stack?', '{lifo,push,pop}'),
  ('Algorithms', 'Easy', 'Explain binary search.', '{sorted,middle,o(log n)}');

INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions)
VALUES ('00000000-0000-0000-0000-000000000001', 'Junior Developer', 'Easy', 15, 4);

INSERT INTO session_questions (session_id, question_id, q_index) VALUES (1, 1, 1), (1, 2, 2);
INSERT INTO responses (session_question_id, answer_text) VALUES (1, 'Last in first out, push and pop.');
INSERT INTO feedback (session_question_id, score, is_correct, matched_keywords, missing_keywords)
VALUES (1, 100, true, '{lifo,push,pop}', '{}'), (2, 0, false, '{}', '{sorted,middle,o(log n)}');

UPDATE sessions SET status = 'completed', completed_at = now(), overall_score = 50 WHERE id = 1;

DO $$ BEGIN
  IF (SELECT count(*) FROM session_questions sq
      LEFT JOIN responses r ON r.session_question_id = sq.id
      WHERE sq.session_id = 1 AND r.id IS NULL) <> 1
  THEN RAISE EXCEPTION 'skipped-question query wrong'; END IF;
END $$;

CREATE FUNCTION expect_fail(stmt TEXT) RETURNS void AS $$
BEGIN
  EXECUTE stmt;
  RAISE EXCEPTION 'expected failure but succeeded: %', stmt USING ERRCODE = 'P0001';
EXCEPTION WHEN OTHERS THEN
  IF SQLSTATE = 'P0001' THEN RAISE; END IF;
END $$ LANGUAGE plpgsql;

SELECT expect_fail($q$INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions) VALUES ('00000000-0000-0000-0000-000000000001', 'x', 'Standard', 15, 4)$q$);
SELECT expect_fail($q$INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions) VALUES ('00000000-0000-0000-0000-000000000001', 'x', 'Easy', 20, 4)$q$);
SELECT expect_fail($q$INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions) VALUES ('00000000-0000-0000-0000-000000000009', 'x', 'Easy', 15, 4)$q$);
SELECT expect_fail($q$INSERT INTO session_questions (session_id, question_id, q_index) VALUES (1, 1, 3)$q$);
SELECT expect_fail($q$INSERT INTO responses (session_question_id, answer_text) VALUES (1, 'again')$q$);
SELECT expect_fail($q$INSERT INTO responses (session_question_id, answer_text) VALUES (2, '   ')$q$);
SELECT expect_fail($q$UPDATE sessions SET completed_at = NULL WHERE id = 1$q$);

DELETE FROM auth.users;
DO $$ BEGIN
  IF (SELECT count(*) FROM sessions) + (SELECT count(*) FROM session_questions)
     + (SELECT count(*) FROM responses) + (SELECT count(*) FROM feedback) <> 0
  THEN RAISE EXCEPTION 'cascade delete failed'; END IF;
END $$;

SELECT 'ALL TESTS PASSED' AS result;
