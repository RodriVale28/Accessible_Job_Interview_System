-- Tests for 003_sprint2.sql. Run on a test database after 001 and 003 (001's test may run first).
-- Rows are looked up by name, not id, so the two test files can share one database.

CREATE OR REPLACE FUNCTION expect_fail(stmt TEXT) RETURNS void AS $$
BEGIN
  EXECUTE stmt;
  RAISE EXCEPTION 'expected failure but succeeded: %', stmt USING ERRCODE = 'P0001';
EXCEPTION WHEN OTHERS THEN
  IF SQLSTATE = 'P0001' THEN RAISE; END IF;
END $$ LANGUAGE plpgsql;

CREATE TEMP VIEW t AS SELECT
  (SELECT id FROM question_library WHERE prompt = 'S2 test: what is a queue?') AS q1,
  (SELECT id FROM question_library WHERE prompt = 'S2 test: tell me about a conflict.') AS q2,
  (SELECT id FROM skills WHERE name = 's2 test sql') AS sk1,
  (SELECT id FROM skills WHERE name = 's2 test communication') AS sk2,
  (SELECT id FROM roles WHERE name = 'S2 Test Analyst') AS r1,
  (SELECT id FROM sessions WHERE job_title = 'S2 test default') AS s1,
  (SELECT id FROM sessions WHERE job_title = 'S2 test mixed') AS s2;

INSERT INTO question_library (category, difficulty, prompt, expected_keywords) VALUES
  ('Data Structures', 'Easy', 'S2 test: what is a queue?', '{fifo}');
INSERT INTO question_library (category, difficulty, prompt, expected_keywords, question_type) VALUES
  ('Teamwork', 'Medium', 'S2 test: tell me about a conflict.', '{situation}', 'Behavioral');
INSERT INTO skills (name) VALUES ('s2 test sql'), ('s2 test communication');
INSERT INTO roles (name, keywords, technical_share) VALUES ('S2 Test Analyst', '{data,sql}', 0.6);
INSERT INTO role_skills (role_id, skill_id, weight) SELECT r1, sk1, 0.7 FROM t;
INSERT INTO role_skills (role_id, skill_id, weight) SELECT r1, sk2, 0.3 FROM t;
INSERT INTO question_skills (question_id, skill_id) SELECT q1, sk1 FROM t;
INSERT INTO question_skills (question_id, skill_id) SELECT q2, sk2 FROM t;
INSERT INTO rubric_criteria (question_id, position, text, keywords)
  SELECT q1, 1, 'Explains that a queue is first in, first out.', '{fifo}' FROM t;
INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions)
  VALUES ('00000000-0000-0000-0000-00000000000b', 'S2 test default', 'Easy', 15, 5);
INSERT INTO sessions (user_id, job_title, interview_type, difficulty, duration_min, total_questions, role_id, timed)
  SELECT '00000000-0000-0000-0000-00000000000b', 'S2 test mixed', 'Mixed', 'Easy', 15, 5, r1, true FROM t;
INSERT INTO session_questions (session_id, question_id, q_index) SELECT s1, q1, 1 FROM t;
INSERT INTO responses (session_id, question_id, answer_text) SELECT s1, q1, 'first in first out' FROM t;
INSERT INTO feedback (session_id, question_id, response_id, score, correct, criteria_met, evidence, grader)
  SELECT s1, q1, (SELECT id FROM responses WHERE session_id = s1), 100, true,
         '{"Explains that a queue is first in, first out."}', '{"first in first out"}', 'ai' FROM t;
INSERT INTO practice_attempts (user_id, question_id, answer_text, result)
  SELECT '00000000-0000-0000-0000-00000000000b', q1, 'fifo', '{"score": 50}' FROM t;
INSERT INTO user_settings (user_id) VALUES ('00000000-0000-0000-0000-00000000000b');

-- Defaults
DO $$ BEGIN
  IF (SELECT question_type FROM question_library, t WHERE id = q1) <> 'Technical' THEN RAISE EXCEPTION 'question_type default'; END IF;
  IF (SELECT timed OR role_id IS NOT NULL OR interview_type <> 'Technical' FROM sessions, t WHERE id = s1) THEN RAISE EXCEPTION 'session defaults'; END IF;
  IF (SELECT criteria_missed <> '{}' OR reasons <> '{}' FROM feedback, t WHERE session_id = s1) THEN RAISE EXCEPTION 'feedback defaults'; END IF;
  IF (SELECT text_size <> 'md' OR theme <> 'light' OR font <> 'default' OR read_aloud FROM user_settings
      WHERE user_id = '00000000-0000-0000-0000-00000000000b') THEN RAISE EXCEPTION 'settings defaults'; END IF;
END $$;

-- skills, roles, role_skills
SELECT expect_fail($q$INSERT INTO skills (name) VALUES ('s2 test sql')$q$);
SELECT expect_fail($q$INSERT INTO skills (name) VALUES ('S2 Test Upper')$q$);
SELECT expect_fail($q$INSERT INTO roles (name, technical_share) VALUES ('S2 Test Analyst', 0.5)$q$);
SELECT expect_fail($q$INSERT INTO roles (name, technical_share) VALUES ('S2 Test Support', 1.5)$q$);
SELECT expect_fail($q$INSERT INTO role_skills (role_id, skill_id, weight) SELECT r1, sk1, 0.5 FROM t$q$);
SELECT expect_fail($q$UPDATE role_skills SET weight = 0 FROM t WHERE role_id = r1$q$);

-- question types, skill tags, rubrics
SELECT expect_fail($q$UPDATE question_library SET question_type = 'Trivia' FROM t WHERE id = q1$q$);
SELECT expect_fail($q$INSERT INTO question_skills (question_id, skill_id) SELECT q1, sk1 FROM t$q$);
SELECT expect_fail($q$INSERT INTO rubric_criteria (question_id, position, text) SELECT q1, 1, 'Duplicate position.' FROM t$q$);
SELECT expect_fail($q$INSERT INTO rubric_criteria (question_id, position, text) SELECT q1, 0, 'Zero position.' FROM t$q$);
SELECT expect_fail($q$INSERT INTO rubric_criteria (question_id, position, text) SELECT q1, 2, '  ' FROM t$q$);

-- sessions
SELECT expect_fail($q$UPDATE sessions SET interview_type = 'Trivia' FROM t WHERE id = s1$q$);
SELECT expect_fail($q$UPDATE sessions SET role_id = -1 FROM t WHERE id = s1$q$);
UPDATE sessions SET interview_type = 'Behavioral' FROM t WHERE id = s1;

-- feedback, settings, practice
SELECT expect_fail($q$UPDATE feedback SET grader = 'human' FROM t WHERE session_id = s1$q$);
SELECT expect_fail($q$UPDATE user_settings SET text_size = 'huge' WHERE user_id = '00000000-0000-0000-0000-00000000000b'$q$);
SELECT expect_fail($q$UPDATE user_settings SET theme = 'neon' WHERE user_id = '00000000-0000-0000-0000-00000000000b'$q$);
SELECT expect_fail($q$UPDATE user_settings SET font = 'comic' WHERE user_id = '00000000-0000-0000-0000-00000000000b'$q$);
SELECT expect_fail($q$INSERT INTO user_settings (user_id) VALUES ('00000000-0000-0000-0000-00000000000b')$q$);
SELECT expect_fail($q$INSERT INTO practice_attempts (user_id, question_id, result) VALUES (gen_random_uuid(), -1, '{}')$q$);

-- Deleting a question removes its tags and rubric; deleting a role removes its weights
CREATE TEMP TABLE ids AS SELECT * FROM t;
DELETE FROM practice_attempts WHERE user_id = '00000000-0000-0000-0000-00000000000b';
DELETE FROM sessions WHERE user_id = '00000000-0000-0000-0000-00000000000b';
DELETE FROM question_library USING ids WHERE id = q1;
DELETE FROM roles USING ids WHERE id = r1;
DO $$ BEGIN
  IF (SELECT count(*) FROM rubric_criteria, ids WHERE question_id = q1)
   + (SELECT count(*) FROM question_skills, ids WHERE question_id = q1)
   + (SELECT count(*) FROM role_skills, ids WHERE role_id = r1) <> 0
  THEN RAISE EXCEPTION 'cascade delete failed'; END IF;
  IF (SELECT count(*) FROM question_skills, ids WHERE question_id = q2) <> 1 THEN RAISE EXCEPTION 'other question lost its tag'; END IF;
  IF (SELECT count(*) FROM skills WHERE name LIKE 's2 test %') <> 2 THEN RAISE EXCEPTION 'skills rows lost'; END IF;
END $$;

SELECT 'ALL TESTS PASSED' AS result;
