export type Operation = '+' | '-' | '*' | '/';

export interface Problem {
  a: number;
  b: number;
  op: Operation;
}

export interface Trick {
  name: string;
  explanation: string;
  operation: Operation;
  matches: (problem: Problem) => boolean;
}

export interface Plan {
  id: string;
  name: string;
  description: string;
  operations: readonly Operation[];
}

export interface TrickProgress {
  attempts: number;
  correct: number;
  streak: number;
  lastPracticed: string | null;
}

export interface TaggedProblemData {
  a: number;
  b: number;
  op: Operation;
  trickName: string;
}

export interface SessionState {
  queue: TaggedProblemData[];
  total: number;
  answered: number;
  correct: number;
}

export interface Profile {
  version: 1;
  name: string;
  planId: string;
  createdAt: string;
  progress: Record<string, TrickProgress>;
  session: SessionState | null;
}

export const MASTERY_STREAK = 5;

export function answerFor(problem: Problem): number {
  switch (problem.op) {
    case '+': return problem.a + problem.b;
    case '-': return problem.a - problem.b;
    case '*': return problem.a * problem.b;
    case '/': return Math.floor(problem.a / problem.b);
  }
}

export function operationLabel(operation: Operation): string {
  return ({ '+': 'Addition', '-': 'Subtraction', '*': 'Multiplication', '/': 'Division' })[operation];
}

export function displayOperator(operation: Operation): string {
  return operation === '*' ? '×' : operation === '/' ? '÷' : operation;
}
