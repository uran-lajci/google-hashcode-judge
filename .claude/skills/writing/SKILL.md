---
name: writing
description: Plain-English rules for prose in this repository, such as docs, READMEs, rules files, skills, commit messages, PR descriptions, GitHub issues and code comments. Never for code or identifiers. Use whenever writing or editing any of these, when asked to make text clearer or shorter, or when text reads like AI.
---

# Writing

Readers here are Hash Code contestants, students and researchers from many countries, many reading in their second or
third language. Write so a reader with intermediate English understands each sentence on the first read.

## Words

- Use the short common word: use (not utilize or leverage), start (not initiate), help (not facilitate), make sure (not
  ensure), before (not prior to), about (not regarding), get (not obtain), show (not demonstrate), also (not
  additionally or furthermore).
- Give one thing one name. Use the terms from `rules/judges.md`: input file, output file, judge, score. Do not
  alternate "output file" with "submission" or "solution file".
- Keep problem terms exactly as the statement writes them, such as library, ride, drone, warehouse or vehicle. Do not
  swap a precise term for a vaguer common word.
- Name a problem by year, round and title: "2020 Qualification Round, Book scanning".
- No marketing words: seamless, robust, powerful, cutting-edge, effortless, comprehensive.
- No filler: "it is important to note that", "in order to", "basically", "simply".
- American spelling: behavior, serialize, analyze, license.

## Sentences

- Active voice, with the actor named: "the worker reads the view", not "the view is read".
- An action is a verb: "check the text", not "perform a check of the text".
- Keep sentences under about 20 words. Split a longer one into two.
- One instruction per sentence. Put a condition before its instruction: "If the token is expired, return 401."
- Steps go in a numbered list, one action per step, in the imperative.
- One topic per paragraph.

## Commits, PRs and issues

- Commit title: `<type>: <summary>`, as in `git log` (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`). The summary
  is imperative and lowercase, with no period.
- A commit body or PR description says why the change is needed and what a reviewer should check. The diff already
  shows what changed.
- A commit that adds a judge names the problem in the summary: `feat: add judge for book_scanning`.

## Before you return text

1. Write only what was asked: no preamble, no closing summary.
2. Read each sentence once more. Split any over 20 words, make passive voice active, and replace any word from the
   lists above.