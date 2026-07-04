import { MASTERY_STREAK, Operation, Problem, Profile, TaggedProblemData, Trick, answerFor } from './models';
import { getPlan } from './plans';
import { TRICKS, TRICKS_BY_NAME } from './tricks';

export const SESSION_LENGTH = 10;

export function factSpace(): Problem[] {
  const facts: Problem[] = [];
  for (let a = 0; a <= 12; a++) for (let b = 0; b <= 12; b++) facts.push({ a, b, op: '+' });
  for (let a = 0; a <= 20; a++) for (let b = 0; b <= a; b++) facts.push({ a, b, op: '-' });
  for (let a = 0; a <= 12; a++) for (let b = 0; b <= 12; b++) facts.push({ a, b, op: '*' });
  for (let b = 1; b <= 12; b++) for (let quotient = 1; quotient <= 12; quotient++) facts.push({ a: b * quotient, b, op: '/' });
  return facts;
}

const FACTS = factSpace();
const pools = new Map<string, readonly Problem[]>();

export function problemsForTrick(trick: Trick): readonly Problem[] {
  let pool = pools.get(trick.name);
  if (!pool) {
    pool = FACTS.filter((problem) => trick.matches(problem));
    pools.set(trick.name, pool);
  }
  return pool;
}

function weightedChoice<T>(items: readonly T[], weights: readonly number[]): T {
  const total = weights.reduce((sum, weight) => sum + weight, 0);
  let target = Math.random() * total;
  for (let index = 0; index < items.length; index++) {
    target -= weights[index];
    if (target <= 0) return items[index];
  }
  return items[items.length - 1];
}

export function startSession(profile: Profile, length = SESSION_LENGTH): void {
  const plan = getPlan(profile.planId);
  const tricks = TRICKS.filter((item) => plan.operations.includes(item.operation) && problemsForTrick(item).length > 0);
  const weights = tricks.map((item) => {
    const progress = profile.progress[item.name];
    return progress?.streak >= MASTERY_STREAK ? 1 : 8 / (1 + (progress?.correct ?? 0));
  });
  const queue: TaggedProblemData[] = [];
  const seen = new Set<string>();
  for (let index = 0; index < length; index++) {
    const selected = weightedChoice(tricks, weights);
    const pool = problemsForTrick(selected);
    let problem = pool[Math.floor(Math.random() * pool.length)];
    for (let retry = 0; retry < 5 && seen.has(problemKey(problem)) && pool.length > seen.size; retry++) {
      problem = pool[Math.floor(Math.random() * pool.length)];
    }
    seen.add(problemKey(problem));
    queue.push({ ...problem, trickName: selected.name });
  }
  profile.session = { queue, total: queue.length, answered: 0, correct: 0 };
}

export function submitAnswer(profile: Profile, answer: number): { correct: boolean; expected: number; trick: Trick } {
  const session = profile.session;
  if (!session?.queue.length) throw new Error('No active question');
  const current = session.queue.shift()!;
  const expected = answerFor(current);
  const correct = answer === expected;
  const progress = profile.progress[current.trickName] ?? { attempts: 0, correct: 0, streak: 0, lastPracticed: null };
  progress.attempts += 1;
  progress.correct += correct ? 1 : 0;
  progress.streak = correct ? progress.streak + 1 : 0;
  progress.lastPracticed = new Date().toISOString();
  profile.progress[current.trickName] = progress;
  session.answered += 1;
  session.correct += correct ? 1 : 0;
  const selectedTrick = TRICKS_BY_NAME.get(current.trickName);
  if (!selectedTrick) throw new Error('Saved session refers to an unknown trick');
  if (session.queue.length === 0) profile.session = null;
  return { correct, expected, trick: selectedTrick };
}

export function isValidSession(profile: Profile): boolean {
  return !!profile.session?.queue.length && profile.session.queue.every((item) =>
    TRICKS_BY_NAME.has(item.trickName) && ['+', '-', '*', '/'].includes(item.op as Operation),
  );
}

function problemKey(problem: Problem): string {
  return `${problem.a}:${problem.op}:${problem.b}`;
}
