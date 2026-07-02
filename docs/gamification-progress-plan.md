# Spoken Kannada Progress, Gamification, and Exams Plan

## Product Notes

The learning loop should reward real spoken Kannada practice, not just page visits. A learner completes a sentence only after pressing Practice Kannada and getting a correct speech check. A chapter is complete only when every practice sentence in that chapter is complete.

## Core Rules

- Every chapter contains many sentence-level practice cards.
- Every speech attempt is saved, whether correct or incorrect.
- A sentence is marked complete after the first correct answer.
- Attempts continue to be tracked after completion, but the first completion controls the chapter-completion milestone.
- More retries should still be encouraging, but they earn fewer points than first-try correctness.
- A chapter is complete when completed sentence count equals the chapter's total practice-card count.
- When a chapter is complete, the learner receives a fun certificate.
- The home page should show chapter status: not started, in progress, or completed.
- Progress views should show completion date/time, total points, and attempt count.

## Scoring Model

- Base score per sentence: 100 points.
- Retry penalty: 15 points per earlier attempt before the first correct attempt.
- Minimum completion score: 25 points.
- Example:
  - correct on first try: 100
  - correct on second try: 85
  - correct on third try: 70
  - many retries: never below 25

This keeps kids encouraged while still making first-try accuracy meaningful.

## Certificates

- Award one chapter certificate when all sentence cards are completed.
- Store the award timestamp.
- Store chapter number, total scenes, completed scenes, total points, and total attempts in certificate metadata.
- Later, certificates can become printable pages with the learner name and completion date.

## Exams

Exam mode should look similar to a chapter, but it should hide the Kannada prompt:

- Show only the English sentence.
- Ask the learner to say the Kannada version from memory.
- Use the same Sarvam speech-to-text checking path.
- Save exam attempts separately from lesson practice.
- Award exam points and pass/fail status.
- Later, use exam results to unlock a larger certificate, such as "Level 1 Spoken Kannada".

## Review and Flashcards

The app should identify harder sentences automatically:

- Many attempts before completion.
- Low score.
- Recently missed exam questions.

Those sentences can appear in:

- Hard sentence review.
- Flashcards.
- Mixed practice across older chapters.
- Mock exams.

## Badges, Streaks, and Engagement

The app should make progress feel highly visible and game-like:

- Show points at the top of chapter pages and the home page.
- Show completed sentences with a large check mark.
- Show chapter cards as not started, in progress, or 100% complete.
- Award badges for milestones:
  - Newbie: first sentence completed.
  - Point Starter: first 500 points.
  - Chapter Champ: first chapter completed.
  - Streak badges: 3 days, 7 days, 14 days, 30 days.
- Show the current streak prominently near the top of the app.
- Show a GitHub-style recent practice grid with daily check-in squares.
- Encourage the next action, such as "Complete 3 more sentences to keep going."
- Later, add reminder notifications when a learner is about to lose a streak.
- Later, add parent-friendly email reminders and weekly summaries.

The tone should be celebratory, polished, and encouraging. Correct answers should feel like wins.

## Implementation Sequence

1. Save every practice attempt and calculate points.
2. Mark sentence, chapter, and certificate completion from saved progress.
3. Show completed/in-progress chapter status on the home page.
4. Improve the progress page with points, attempts, and certificate details.
5. Show points, badges, and streaks at the top of the chapter and home pages.
6. Add a streak/rewards page with a daily practice grid.
7. Add exam data model and one first mock exam page.
8. Add hard-sentence review and flashcards.
9. Add printable/shareable certificates.
