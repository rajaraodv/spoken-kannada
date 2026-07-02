import Link from "next/link";
import { getCurrentSession } from "@/lib/auth-session";
import { ensureAppUser, getUserProgress } from "@/lib/progress";

export const dynamic = "force-dynamic";

type ChapterProgress = {
  chapter: number;
  total_scenes: number;
  completed_scenes: number;
  total_attempts: number;
  total_points: number;
  completed_at: string | null;
  certificate_awarded_at: string | null;
};

type Certificate = {
  id: string;
  title: string;
  chapter_start: number | null;
  chapter_end: number | null;
  awarded_at: string;
};

type Badge = {
  key: string;
  label: string;
  icon: string;
  description: string;
};

type StreakCell = {
  date: string;
  count: number;
  level: number;
};

type UserProgress = {
  chapters?: ChapterProgress[];
  certificates?: Certificate[];
  summary?: {
    completedChapters: number;
    completedScenes: number;
    totalAttempts: number;
    totalPoints: number;
    streakDays: number;
    streakGrid: StreakCell[];
    badges: Badge[];
  };
};

function percent(completed: number, total: number) {
  if (!total) return 0;
  return Math.min(100, Math.round((completed / total) * 100));
}

export default async function ProgressPage() {
  const session = await getCurrentSession();

  if (!session) {
    return (
      <main className="min-h-screen bg-[#f8fafc] px-5 py-10 text-slate-950">
        <section className="mx-auto max-w-3xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-slate-500">
            Progress
          </p>
          <h1 className="mt-3 text-4xl font-black tracking-normal">
            Sign in to save practice
          </h1>
          <p className="mt-3 text-lg font-medium leading-8 text-slate-600">
            Correct Kannada speaking attempts will count toward chapter
            completion and certificates.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a
              className="rounded-lg bg-slate-950 px-5 py-3 text-base font-black text-white shadow-sm"
              href="/sign-in?callbackUrl=/progress"
            >
              Sign in with email
            </a>
            <Link
              className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-base font-black text-slate-900 shadow-sm"
              href="/"
            >
              Back to chapters
            </Link>
          </div>
        </section>
      </main>
    );
  }

  const user = await ensureAppUser(session);
  const progress = (user ? await getUserProgress(user.id) : null) as unknown as UserProgress | null;
  const chapters = (progress?.chapters ?? []) as ChapterProgress[];
  const certificates = (progress?.certificates ?? []) as Certificate[];
  const totalCompleted = chapters.reduce(
    (sum, chapter) => sum + Number(chapter.completed_scenes ?? 0),
    0,
  );
  const totalPoints = chapters.reduce(
    (sum, chapter) => sum + Number(chapter.total_points ?? 0),
    0,
  );
  const totalAttempts = chapters.reduce(
    (sum, chapter) => sum + Number(chapter.total_attempts ?? 0),
    0,
  );
  const streakDays = Number(progress?.summary?.streakDays ?? 0);
  const badges = progress?.summary?.badges ?? [];
  const streakGrid = progress?.summary?.streakGrid ?? [];

  return (
    <main className="min-h-screen bg-[#f8fafc] px-5 py-8 text-slate-950">
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-8">
        <header className="flex flex-col gap-5 border-b border-slate-200 pb-7 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-slate-500">
              Spoken Kannada
            </p>
            <h1 className="mt-3 text-4xl font-black tracking-normal">
              Progress
            </h1>
            <p className="mt-2 text-base font-semibold text-slate-600">
              {session.user?.name || session.user?.email || "Learner"}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-base font-black text-slate-900 shadow-sm"
              href="/"
            >
              Chapters
            </Link>
            <a
              className="rounded-lg bg-slate-950 px-5 py-3 text-base font-black text-white shadow-sm"
              href="/sign-out?callbackUrl=/"
            >
              Sign out
            </a>
          </div>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-500">
              Scenes
            </p>
            <p className="mt-2 text-4xl font-black">{totalCompleted}</p>
            <p className="mt-1 font-semibold text-slate-500">completed</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-500">
              Chapters
            </p>
            <p className="mt-2 text-4xl font-black">
              {chapters.filter((chapter) => chapter.completed_at).length}
            </p>
            <p className="mt-1 font-semibold text-slate-500">finished</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-500">
              Certificates
            </p>
            <p className="mt-2 text-4xl font-black">{certificates.length}</p>
            <p className="mt-1 font-semibold text-slate-500">earned</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-500">
              Points
            </p>
            <p className="mt-2 text-4xl font-black">{totalPoints}</p>
            <p className="mt-1 font-semibold text-slate-500">
              across {totalAttempts} tries
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-500">
              Streak
            </p>
            <p className="mt-2 text-4xl font-black">{streakDays}</p>
            <p className="mt-1 font-semibold text-slate-500">days in a row</p>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[1fr_auto]">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-2xl font-black">Badges</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {badges.length ? (
                badges.map((badge) => (
                  <span
                    key={badge.key}
                    className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-black text-slate-800"
                    title={badge.description}
                  >
                    {badge.icon} {badge.label}
                  </span>
                ))
              ) : (
                <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-black text-slate-500">
                  Complete one sentence to earn Newbie
                </span>
              )}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-2xl font-black">Streak Map</h2>
            <div className="mt-4 grid gap-1" style={{ gridTemplateColumns: "repeat(14, 0.75rem)" }}>
              {(streakGrid.length ? streakGrid : Array.from({ length: 28 }, (_, index) => ({ date: String(index), count: 0, level: 0 }))).map((cell) => (
                <span
                  key={cell.date}
                  title={`${cell.date}: ${cell.count} tries`}
                  className={
                    cell.level >= 4
                      ? "h-3 w-3 rounded-[3px] bg-emerald-800"
                      : cell.level === 3
                        ? "h-3 w-3 rounded-[3px] bg-emerald-500"
                        : cell.level === 2
                          ? "h-3 w-3 rounded-[3px] bg-emerald-300"
                          : cell.level === 1
                            ? "h-3 w-3 rounded-[3px] bg-emerald-200"
                            : "h-3 w-3 rounded-[3px] bg-slate-200"
                  }
                />
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-2xl font-black">Chapter Completion</h2>
          <div className="mt-5 grid gap-4">
            {chapters.length === 0 ? (
              <p className="font-semibold text-slate-500">
                No saved practice yet. Open a chapter, sign in, and complete a
                Kannada practice card.
              </p>
            ) : (
              chapters.map((chapter) => {
                const value = percent(
                  Number(chapter.completed_scenes ?? 0),
                  Number(chapter.total_scenes ?? 0),
                );
                return (
                  <Link
                    key={chapter.chapter}
                    className="rounded-xl border border-slate-200 p-4 transition hover:border-slate-400"
                    href={`/chapters/chapter-${String(chapter.chapter).padStart(2, "0")}.html`}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-black">
                          Chapter {chapter.chapter}
                        </h3>
                        <p className="mt-1 font-semibold text-slate-500">
                          {chapter.completed_scenes} of {chapter.total_scenes}{" "}
                          scenes complete
                        </p>
                        <p className="mt-1 font-semibold text-slate-500">
                          {chapter.total_points} points · {chapter.total_attempts} tries
                        </p>
                        {chapter.completed_at ? (
                          <p className="mt-1 font-semibold text-emerald-700">
                            Completed{" "}
                            {new Date(chapter.completed_at).toLocaleString()}
                          </p>
                        ) : null}
                      </div>
                      <span className="text-lg font-black">{value}%</span>
                    </div>
                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-slate-950"
                        style={{ width: `${value}%` }}
                      />
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-2xl font-black">Certificates</h2>
          <div className="mt-5 grid gap-3">
            {certificates.length === 0 ? (
              <p className="font-semibold text-slate-500">
                Certificates appear here after chapter completion.
              </p>
            ) : (
              certificates.map((certificate) => (
                <div
                  key={certificate.id}
                  className="rounded-xl border border-slate-200 p-4"
                >
                  <h3 className="text-lg font-black">{certificate.title}</h3>
                  <p className="mt-1 font-semibold text-slate-500">
                    Awarded {new Date(certificate.awarded_at).toLocaleDateString()}
                  </p>
                  {certificate.chapter_start ? (
                    <p className="mt-1 font-semibold text-slate-500">
                      Chapter {certificate.chapter_start}
                    </p>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </section>
      </section>
    </main>
  );
}
