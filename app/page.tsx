import fs from "node:fs";
import path from "node:path";
import type { CSSProperties } from "react";
import { getCurrentSession } from "@/lib/auth-session";
import { chapterTitleMap, chapterTotals, ensureAppUser, getUserProgress } from "@/lib/progress";

export const dynamic = "force-dynamic";

type ChapterLink = {
  number: number;
  href: string;
  title?: string;
  totalScenes?: number;
};

type ChapterProgress = {
  chapter: number;
  total_scenes: number;
  completed_scenes: number;
  total_attempts: number;
  total_points: number;
  completed_at: string | null;
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

function getChapters(): ChapterLink[] {
  const chaptersDir = path.join(process.cwd(), "public", "chapters");
  const titles = chapterTitleMap();
  const totals = new Map(chapterTotals().map((chapter) => [chapter.chapter, chapter.totalScenes]));
  return fs
    .readdirSync(chaptersDir)
    .reduce<ChapterLink[]>((acc, file) => {
      const match = file.match(/^chapter-(\d{2})\.html$/);
      if (!match) return acc;
      acc.push({
        number: Number(match[1]),
        href: `/chapters/${file}`,
        title: titles.get(Number(match[1])),
        totalScenes: totals.get(Number(match[1])) ?? 0,
      });
      return acc;
    }, [])
    .sort((a, b) => a.number - b.number);
}

async function getProgress() {
  const session = await getCurrentSession();
  if (!session || !(process.env.DATABASE_URL || process.env.POSTGRES_URL)) {
    return null;
  }

  try {
    const user = await ensureAppUser(session);
    if (!user) return null;
    return (await getUserProgress(user.id)) as unknown as UserProgress;
  } catch {
    return null;
  }
}

export default async function Home() {
  const chapters = getChapters();
  const accents = [
    { accent: "#2563eb", soft: "#eff6ff" },
    { accent: "#0f766e", soft: "#ecfdf5" },
    { accent: "#c2410c", soft: "#fff7ed" },
    { accent: "#7c3aed", soft: "#f5f3ff" },
    { accent: "#be123c", soft: "#fff1f2" },
    { accent: "#047857", soft: "#ecfdf5" },
  ];
  const progress = await getProgress();
  const progressByChapter = new Map(
    ((progress?.chapters ?? []) as ChapterProgress[]).map((chapter) => [
      Number(chapter.chapter),
      chapter,
    ]),
  );
  const completedCount = Array.from(progressByChapter.values()).filter(
    (chapter) => chapter.completed_at,
  ).length;
  const totalPoints = Number(progress?.summary?.totalPoints ?? Array.from(progressByChapter.values()).reduce(
    (sum, chapter) => sum + Number(chapter.total_points ?? 0),
    0,
  ));
  const streakDays = Number(progress?.summary?.streakDays ?? 0);
  const badges = progress?.summary?.badges ?? [];
  const streakGrid = progress?.summary?.streakGrid ?? [];

  return (
    <main className="min-h-screen bg-[#f8fafc] text-slate-950">
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-5 py-8 sm:px-8 lg:py-12">
        <header className="flex flex-col gap-5 border-b border-slate-200 pb-8">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.18em] text-teal-700">
              Spoken Kannada
            </p>
            <h1 className="mt-3 max-w-3xl text-4xl font-black leading-tight tracking-normal sm:text-5xl">
              Practice Kannada by chapter
            </h1>
          </div>
          <p className="max-w-3xl text-lg font-medium leading-8 text-slate-600">
            This app now uses the generated chapter pages: visual conversation
            cards, English and Kannada audio, and Kannada speech practice.
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-400">
                Completed
              </p>
              <p className="mt-1 text-3xl font-black">{completedCount}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-400">
                Points
              </p>
              <p className="mt-1 text-3xl font-black">{totalPoints}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-400">
                Chapters
              </p>
              <p className="mt-1 text-3xl font-black">{chapters.length}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-bold uppercase tracking-[0.14em] text-slate-400">
                Streak
              </p>
              <p className="mt-1 text-3xl font-black">{streakDays} days</p>
            </div>
          </div>
          <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[1fr_auto]">
            <div>
              <p className="text-sm font-black uppercase tracking-[0.14em] text-slate-400">
                Badges
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
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
            <div>
              <p className="text-sm font-black uppercase tracking-[0.14em] text-slate-400">
                Daily practice
              </p>
              <div className="mt-3 grid gap-1" style={{ gridTemplateColumns: "repeat(14, 0.75rem)" }}>
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
          </div>
          <div className="flex flex-wrap gap-3">
            <a
              className="rounded-lg bg-teal-700 px-5 py-3 text-base font-black text-white shadow-sm transition hover:bg-teal-800"
              href="/chapters/chapter-03.html"
            >
              Open Chapter 03
            </a>
            <a
              className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-base font-black text-slate-900 shadow-sm transition hover:border-teal-600 hover:text-teal-800"
              href="/conversations-page-by-page.html"
            >
              Open generated index
            </a>
            <a
              className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-base font-black text-slate-900 shadow-sm transition hover:border-teal-600 hover:text-teal-800"
              href="/progress"
            >
              View progress
            </a>
            <a
              className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-base font-black text-slate-900 shadow-sm transition hover:border-teal-600 hover:text-teal-800"
              href="/sign-in"
            >
              Sign in
            </a>
          </div>
        </header>

        <section aria-labelledby="chapter-list-heading">
          <div className="mb-4 flex items-end justify-between gap-4">
            <div>
              <h2 id="chapter-list-heading" className="text-2xl font-black">
                Chapters
              </h2>
              <p className="mt-1 font-semibold text-slate-500">
                {chapters.length} generated chapter pages
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {chapters.map((chapter) => {
              const accent = accents[(chapter.number - 1) % accents.length];
              const progress = progressByChapter.get(chapter.number);
              const totalScenes = Number(progress?.total_scenes ?? chapter.totalScenes ?? 0);
              const completedScenes = Number(progress?.completed_scenes ?? 0);
              const percent = totalScenes
                ? Math.min(100, Math.round((completedScenes / totalScenes) * 100))
                : 0;
              const completed = Boolean(progress?.completed_at);
              const started = completedScenes > 0 || Number(progress?.total_attempts ?? 0) > 0;
              return (
                <a
                  key={chapter.number}
                  href={chapter.href}
                  style={
                    {
                      "--chapter-accent": accent.accent,
                      "--chapter-soft": accent.soft,
                    } as CSSProperties
                  }
                  className="group relative min-h-[218px] overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-50 p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg"
                >
                  <span className="absolute inset-x-0 top-0 h-1.5 bg-[var(--chapter-accent)]" />
                  <span className="absolute -right-9 -top-11 h-32 w-32 rounded-full bg-[var(--chapter-soft)]" />
                  <div className="flex items-start justify-between gap-4">
                    <div className="relative">
                      <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-400">
                        Chapter
                      </p>
                      <h3 className="mt-1 text-3xl font-black leading-none text-slate-950">
                        {String(chapter.number).padStart(2, "0")}
                      </h3>
                    </div>
                    <span
                      className={
                        completed
                          ? "relative rounded-full bg-emerald-100 px-3 py-2 text-sm font-black text-emerald-800"
                          : started
                            ? "relative rounded-full px-3 py-2 text-sm font-black text-[var(--chapter-accent)]"
                            : "relative rounded-full px-3 py-2 text-sm font-black text-[var(--chapter-accent)]"
                      }
                      style={completed ? undefined : { background: accent.soft }}
                    >
                      {completed ? "✓ 100% complete" : started ? "In progress" : "Start"}
                    </span>
                  </div>
                  <div className="relative mt-4 grid gap-2">
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-slate-400">
                      Concept
                    </p>
                    <h3 className="line-clamp-2 text-lg font-black leading-snug text-slate-950">
                      {chapter.title || "Everyday conversation"}
                    </h3>
                    <p className="text-sm font-bold text-slate-500">
                      Practice the core phrases in this chapter.
                    </p>
                  </div>
                  <div className="relative mt-4">
                    <div className="flex justify-between text-sm font-black text-slate-500">
                      <span>
                        {completedScenes} / {totalScenes || "?"} sentences
                      </span>
                      <span>{percent}%</span>
                    </div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={completed ? "h-full rounded-full bg-emerald-600" : "h-full rounded-full bg-[var(--chapter-accent)]"}
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-slate-500">
                        {started ? "Keep going" : "Ready to start"}
                      </span>
                      <span className={completed ? "rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-black text-emerald-700" : "rounded-full bg-slate-100 px-3 py-1.5 text-sm font-black text-slate-800"}>
                        {Number(progress?.total_points ?? 0)} pts · {Number(progress?.total_attempts ?? 0)} tries
                      </span>
                    </div>
                  </div>
                </a>
              );
            })}
          </div>
        </section>
      </section>
    </main>
  );
}
