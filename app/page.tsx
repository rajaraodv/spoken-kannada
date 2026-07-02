import fs from "node:fs";
import path from "node:path";

type ChapterLink = {
  number: number;
  href: string;
};

function getChapters(): ChapterLink[] {
  const chaptersDir = path.join(process.cwd(), "public", "chapters");
  return fs
    .readdirSync(chaptersDir)
    .map((file) => {
      const match = file.match(/^chapter-(\d{2})\.html$/);
      if (!match) return null;
      return {
        number: Number(match[1]),
        href: `/chapters/${file}`,
      };
    })
    .filter((chapter): chapter is ChapterLink => chapter !== null)
    .sort((a, b) => a.number - b.number);
}

export default function Home() {
  const chapters = getChapters();

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
            {chapters.map((chapter) => (
              <a
                key={chapter.number}
                href={chapter.href}
                className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-teal-500 hover:shadow-md"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-bold uppercase tracking-[0.16em] text-slate-400">
                      Chapter
                    </p>
                    <h3 className="mt-1 text-2xl font-black text-slate-950">
                      {String(chapter.number).padStart(2, "0")}
                    </h3>
                  </div>
                  <span className="rounded-md bg-slate-100 px-3 py-2 text-sm font-black text-slate-700 transition group-hover:bg-teal-100 group-hover:text-teal-800">
                    Open
                  </span>
                </div>
              </a>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
