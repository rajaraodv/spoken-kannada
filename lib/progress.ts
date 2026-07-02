import fs from "node:fs";
import path from "node:path";
import type { AppSession } from "./auth-session";
import { getSql } from "./db";

type AppUser = {
  id: string;
  email: string;
  name: string | null;
  image_url: string | null;
};

type ChapterVisuals = {
  [chapter: string]: {
    theme?: string;
    items?: Array<unknown>;
  };
};

type Curriculum = {
  chapters?: Array<{
    chapter?: number;
    title?: string;
  }>;
};

type ExistingProgress = {
  status: string;
  attempts: number;
  correct_attempts: number;
  points_earned: number;
};

type ChapterProgressRow = {
  chapter: number;
  total_scenes: number;
  completed_scenes: number;
  total_attempts: number;
  total_points: number;
  completed_at: string | null;
  certificate_awarded_at: string | null;
};

type PracticeSceneRow = {
  chapter: number;
  conversation_id: string;
  scene_index: number;
  status: string;
  attempts: number;
  correct_attempts: number;
  points_earned: number;
  first_completed_attempts: number | null;
  completed_at: string | null;
};

let cachedVisuals: ChapterVisuals | null = null;

function chapterVisuals(): ChapterVisuals {
  if (cachedVisuals) return cachedVisuals;
  const file = path.join(process.cwd(), "data", "chapter_visuals.json");
  const parsed = JSON.parse(fs.readFileSync(file, "utf8")) as ChapterVisuals;
  cachedVisuals = parsed;
  return parsed;
}

export function totalScenesForChapter(chapter: number): number {
  return chapterVisuals()[String(chapter)]?.items?.length ?? 0;
}

export function chapterTotals() {
  return Object.entries(chapterVisuals())
    .map(([chapter, value]) => ({
      chapter: Number(chapter),
      totalScenes: value.items?.length ?? 0,
    }))
    .filter((item) => Number.isInteger(item.chapter) && item.chapter > 0)
    .sort((a, b) => a.chapter - b.chapter);
}

export function chapterTitleMap() {
  const file = path.join(process.cwd(), "data", "improved_kids_conversation_curriculum.json");
  try {
    const parsed = JSON.parse(fs.readFileSync(file, "utf8")) as Curriculum;
    return new Map(
      (parsed.chapters ?? [])
        .filter((chapter) => chapter.chapter && chapter.title)
        .map((chapter) => [Number(chapter.chapter), String(chapter.title)]),
    );
  } catch {
    return new Map<number, string>();
  }
}

function pointsForCompletion(attemptNumber: number) {
  return Math.max(25, 100 - Math.max(0, attemptNumber - 1) * 15);
}

export async function ensureAppUser(session: AppSession): Promise<AppUser | null> {
  const email = session.user?.email?.trim().toLowerCase();
  if (!email) return null;

  const sql = getSql();
  const rows = (await sql`
    INSERT INTO app_users (
      auth_provider,
      provider_account_id,
      email,
      name,
      image_url,
      updated_at
    )
    VALUES (
      'neon_email_otp',
      ${session.user?.id || null},
      ${email},
      ${session.user?.name ?? null},
      ${session.user?.image ?? null},
      now()
    )
    ON CONFLICT (email) DO UPDATE
    SET
      provider_account_id = COALESCE(EXCLUDED.provider_account_id, app_users.provider_account_id),
      name = EXCLUDED.name,
      image_url = EXCLUDED.image_url,
      updated_at = now()
    RETURNING id, email, name, image_url
  `) as AppUser[];

  return (rows[0] as AppUser | undefined) ?? null;
}

export async function recordPracticeAttempt(input: {
  userId: string;
  chapter: number;
  conversationId: string;
  sceneIndex: number;
  expected: string;
  transcript: string;
  score: number | null;
  matched: boolean;
}) {
  const sql = getSql();
  const totalScenes = totalScenesForChapter(input.chapter);
  const existingRows = (await sql`
    SELECT status, attempts, correct_attempts, points_earned
    FROM user_progress
    WHERE user_id = ${input.userId}
      AND chapter = ${input.chapter}
      AND conversation_id = ${input.conversationId}
      AND scene_index = ${input.sceneIndex}
  `) as ExistingProgress[];
  const existing = existingRows[0];
  const wasCompleted = existing?.status === "completed";
  const attemptNumber = Number(existing?.attempts ?? 0) + 1;
  const correctAttempts = Number(existing?.correct_attempts ?? 0) + (input.matched ? 1 : 0);
  const pointsAwarded = input.matched && !wasCompleted ? pointsForCompletion(attemptNumber) : 0;
  const totalPointsForScene = Number(existing?.points_earned ?? 0) + pointsAwarded;
  const status = input.matched || wasCompleted ? "completed" : "started";
  const completedAt = input.matched && !wasCompleted ? new Date().toISOString() : null;

  await sql`
    INSERT INTO practice_attempts (
      user_id,
      chapter,
      conversation_id,
      scene_index,
      attempt_number,
      expected,
      transcript,
      score,
      matched,
      points_awarded,
      attempted_at
    )
    VALUES (
      ${input.userId},
      ${input.chapter},
      ${input.conversationId},
      ${input.sceneIndex},
      ${attemptNumber},
      ${input.expected},
      ${input.transcript},
      ${input.score},
      ${input.matched},
      ${pointsAwarded},
      now()
    )
  `;

  await sql`
    INSERT INTO user_progress (
      user_id,
      chapter,
      conversation_id,
      scene_index,
      status,
      attempts,
      correct_attempts,
      points_earned,
      first_completed_attempts,
      best_score,
      last_expected,
      last_transcript,
      last_practiced_at,
      completed_at
    )
    VALUES (
      ${input.userId},
      ${input.chapter},
      ${input.conversationId},
      ${input.sceneIndex},
      ${status},
      ${attemptNumber},
      ${correctAttempts},
      ${totalPointsForScene},
      ${input.matched ? attemptNumber : null},
      ${input.score},
      ${input.expected},
      ${input.transcript},
      now(),
      ${completedAt}
    )
    ON CONFLICT (user_id, chapter, conversation_id, scene_index) DO UPDATE
    SET
      status = EXCLUDED.status,
      attempts = EXCLUDED.attempts,
      correct_attempts = EXCLUDED.correct_attempts,
      points_earned = EXCLUDED.points_earned,
      first_completed_attempts = COALESCE(user_progress.first_completed_attempts, EXCLUDED.first_completed_attempts),
      best_score = GREATEST(
        COALESCE(user_progress.best_score, 0),
        COALESCE(EXCLUDED.best_score, 0)
      ),
      last_expected = EXCLUDED.last_expected,
      last_transcript = EXCLUDED.last_transcript,
      last_practiced_at = now(),
      completed_at = COALESCE(user_progress.completed_at, EXCLUDED.completed_at)
  `;

  const chapterRows = (await sql`
    SELECT
      count(*) FILTER (WHERE status = 'completed')::int AS completed_scenes,
      COALESCE(sum(attempts), 0)::int AS total_attempts,
      COALESCE(sum(points_earned), 0)::int AS total_points
    FROM user_progress
    WHERE user_id = ${input.userId}
      AND chapter = ${input.chapter}
  `) as Array<{ completed_scenes: number; total_attempts: number; total_points: number }>;
  const completedScenes = Number(chapterRows[0]?.completed_scenes ?? 0);
  const totalAttempts = Number(chapterRows[0]?.total_attempts ?? 0);
  const totalPoints = Number(chapterRows[0]?.total_points ?? 0);
  const chapterCompleted = totalScenes > 0 && completedScenes >= totalScenes;
  const chapterCompletedAt = chapterCompleted ? new Date().toISOString() : null;

  await sql`
    INSERT INTO chapter_completion (
      user_id,
      chapter,
      total_scenes,
      completed_scenes,
      total_attempts,
      total_points,
      completed_at,
      updated_at
    )
    VALUES (
      ${input.userId},
      ${input.chapter},
      ${totalScenes},
      ${completedScenes},
      ${totalAttempts},
      ${totalPoints},
      ${chapterCompletedAt},
      now()
    )
    ON CONFLICT (user_id, chapter) DO UPDATE
    SET
      total_scenes = EXCLUDED.total_scenes,
      completed_scenes = EXCLUDED.completed_scenes,
      total_attempts = EXCLUDED.total_attempts,
      total_points = EXCLUDED.total_points,
      completed_at = COALESCE(chapter_completion.completed_at, EXCLUDED.completed_at),
      updated_at = now()
  `;

  if (chapterCompleted) {
    await sql`
      INSERT INTO certificates (
        user_id,
        certificate_type,
        title,
        chapter_start,
        chapter_end,
        metadata
      )
      VALUES (
        ${input.userId},
        'chapter_completion',
        ${`Chapter ${input.chapter} Completion`},
        ${input.chapter},
        ${input.chapter},
        ${JSON.stringify({ totalScenes, completedScenes, totalAttempts, totalPoints })}
      )
      ON CONFLICT (user_id, certificate_type, chapter_start, chapter_end)
      DO NOTHING
    `;

    await sql`
      UPDATE chapter_completion
      SET certificate_awarded_at = COALESCE(certificate_awarded_at, now())
      WHERE user_id = ${input.userId}
        AND chapter = ${input.chapter}
    `;
  }

  return {
    totalScenes,
    completedScenes,
    totalAttempts,
    totalPoints,
    pointsAwarded,
    attemptNumber,
    chapterCompleted,
  };
}

export async function getUserProgress(userId: string) {
  const sql = getSql();
  const [chapters, scenes, certificates, dayRows] = await Promise.all([
    sql`
      SELECT chapter, total_scenes, completed_scenes, total_attempts, total_points, completed_at, certificate_awarded_at
      FROM chapter_completion
      WHERE user_id = ${userId}
      ORDER BY chapter
    `,
    sql`
      SELECT
        chapter,
        conversation_id,
        scene_index,
        status,
        attempts,
        correct_attempts,
        points_earned,
        first_completed_attempts,
        completed_at
      FROM user_progress
      WHERE user_id = ${userId}
      ORDER BY chapter, scene_index
    `,
    sql`
      SELECT id, certificate_type, title, chapter_start, chapter_end, awarded_at, metadata
      FROM certificates
      WHERE user_id = ${userId}
      ORDER BY awarded_at DESC
    `,
    sql`
      SELECT attempted_at::date AS practice_day, count(*)::int AS attempt_count
      FROM practice_attempts
      WHERE user_id = ${userId}
      GROUP BY attempted_at::date
      ORDER BY attempted_at::date DESC
      LIMIT 120
    `,
  ]);

  const chapterRows = chapters as ChapterProgressRow[];
  const sceneRows = scenes as PracticeSceneRow[];
  const totalPoints = chapterRows.reduce(
    (sum, chapter) => sum + Number(chapter.total_points ?? 0),
    0,
  );
  const completedChapters = chapterRows.filter((chapter) => chapter.completed_at).length;
  const completedScenes = sceneRows.filter((scene) => scene.status === "completed").length;
  const totalAttempts = sceneRows.reduce((sum, scene) => sum + Number(scene.attempts ?? 0), 0);
  const practiceDays = dayRows as Array<{ practice_day: string; attempt_count: number }>;
  const streakDays = currentStreakDays(practiceDays.map((row) => row.practice_day));
  const streakGrid = recentStreakGrid(practiceDays);
  const badges = earnedBadges({
    completedChapters,
    completedScenes,
    totalPoints,
    streakDays,
  });

  return {
    chapters,
    scenes,
    certificates,
    summary: {
      completedChapters,
      completedScenes,
      totalAttempts,
      totalPoints,
      streakDays,
      streakGrid,
      badges,
    },
  };
}

function earnedBadges(input: {
  completedChapters: number;
  completedScenes: number;
  totalPoints: number;
  streakDays: number;
}) {
  const badges = [];
  if (input.completedScenes >= 1) {
    badges.push({ key: "newbie", label: "Newbie", icon: "🌱", description: "Completed your first Kannada sentence." });
  }
  if (input.totalPoints >= 500) {
    badges.push({ key: "point_starter", label: "Point Starter", icon: "⭐", description: "Earned 500 points." });
  }
  if (input.completedChapters >= 1) {
    badges.push({ key: "chapter_champ", label: "Chapter Champ", icon: "🏅", description: "Finished a full chapter." });
  }
  if (input.streakDays >= 3) {
    badges.push({ key: "streak_3", label: "3-Day Streak", icon: "🔥", description: "Practiced three days in a row." });
  }
  return badges;
}

function currentStreakDays(days: string[]) {
  const seen = new Set(days.map((day) => new Date(day).toISOString().slice(0, 10)));
  if (!seen.size) return 0;
  const cursor = new Date();
  cursor.setHours(0, 0, 0, 0);
  let streak = 0;
  for (let offset = 0; offset < 120; offset += 1) {
    const key = cursor.toISOString().slice(0, 10);
    if (!seen.has(key)) {
      if (offset === 0) {
        cursor.setDate(cursor.getDate() - 1);
        continue;
      }
      break;
    }
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

function recentStreakGrid(days: Array<{ practice_day: string; attempt_count: number }>) {
  const counts = new Map(
    days.map((day) => [
      new Date(day.practice_day).toISOString().slice(0, 10),
      Number(day.attempt_count ?? 0),
    ]),
  );
  const cells = [];
  const cursor = new Date();
  cursor.setHours(0, 0, 0, 0);
  cursor.setDate(cursor.getDate() - 27);
  for (let index = 0; index < 28; index += 1) {
    const key = cursor.toISOString().slice(0, 10);
    const count = counts.get(key) ?? 0;
    cells.push({
      date: key,
      count,
      active: count > 0,
      level: count >= 8 ? 4 : count >= 4 ? 3 : count >= 2 ? 2 : count >= 1 ? 1 : 0,
    });
    cursor.setDate(cursor.getDate() + 1);
  }
  return cells;
}
