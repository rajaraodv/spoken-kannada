CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_provider text NOT NULL DEFAULT 'neon_email_otp',
  provider_account_id text,
  email text NOT NULL UNIQUE,
  name text,
  image_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_progress (
  user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  chapter integer NOT NULL,
  conversation_id text NOT NULL,
  scene_index integer NOT NULL,
  status text NOT NULL DEFAULT 'started',
  attempts integer NOT NULL DEFAULT 0,
  correct_attempts integer NOT NULL DEFAULT 0,
  points_earned integer NOT NULL DEFAULT 0,
  first_completed_attempts integer,
  best_score numeric(6, 5),
  last_expected text,
  last_transcript text,
  last_practiced_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  PRIMARY KEY (user_id, chapter, conversation_id, scene_index)
);

ALTER TABLE IF EXISTS user_progress
  ADD COLUMN IF NOT EXISTS points_earned integer NOT NULL DEFAULT 0;

ALTER TABLE IF EXISTS user_progress
  ADD COLUMN IF NOT EXISTS first_completed_attempts integer;

CREATE INDEX IF NOT EXISTS user_progress_user_chapter_idx
  ON user_progress (user_id, chapter);

CREATE TABLE IF NOT EXISTS practice_attempts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  chapter integer NOT NULL,
  conversation_id text NOT NULL,
  scene_index integer NOT NULL,
  attempt_number integer NOT NULL,
  expected text,
  transcript text,
  score numeric(6, 5),
  matched boolean NOT NULL DEFAULT false,
  points_awarded integer NOT NULL DEFAULT 0,
  attempted_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS practice_attempts_user_chapter_scene_idx
  ON practice_attempts (user_id, chapter, conversation_id, scene_index);

CREATE INDEX IF NOT EXISTS practice_attempts_user_attempted_at_idx
  ON practice_attempts (user_id, attempted_at DESC);

CREATE TABLE IF NOT EXISTS chapter_completion (
  user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  chapter integer NOT NULL,
  total_scenes integer NOT NULL DEFAULT 0,
  completed_scenes integer NOT NULL DEFAULT 0,
  total_attempts integer NOT NULL DEFAULT 0,
  total_points integer NOT NULL DEFAULT 0,
  completed_at timestamptz,
  certificate_awarded_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, chapter)
);

ALTER TABLE IF EXISTS chapter_completion
  ADD COLUMN IF NOT EXISTS total_attempts integer NOT NULL DEFAULT 0;

ALTER TABLE IF EXISTS chapter_completion
  ADD COLUMN IF NOT EXISTS total_points integer NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS certificates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  certificate_type text NOT NULL,
  title text NOT NULL,
  chapter_start integer,
  chapter_end integer,
  awarded_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (user_id, certificate_type, chapter_start, chapter_end)
);

CREATE TABLE IF NOT EXISTS mock_exam_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  exam_key text NOT NULL,
  score numeric(6, 5),
  passed boolean NOT NULL DEFAULT false,
  answers jsonb NOT NULL DEFAULT '[]'::jsonb,
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS mock_exam_attempts_user_id_idx
  ON mock_exam_attempts (user_id);
