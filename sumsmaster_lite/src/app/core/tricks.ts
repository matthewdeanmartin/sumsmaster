import { Problem, Trick } from './models';

const trick = (
  name: string,
  explanation: string,
  operation: Trick['operation'],
  matches: (problem: Problem) => boolean,
): Trick => ({ name, explanation, operation, matches: (problem) => problem.op === operation && matches(problem) });

const near = (value: number, target: number, window = 2): boolean =>
  Math.abs(value - target) > 0 && Math.abs(value - target) <= window;

const powerOfTen = (value: number): boolean => {
  if (value <= 0) return false;
  while (value % 10 === 0) value /= 10;
  return value === 1;
};

export const TRICKS: readonly Trick[] = [
  trick('add 0 (identity)', 'a + 0 = a', '+', (p) => p.a === 0 || p.b === 0),
  trick('add 1 (count up)', 'a + 1 is the next number', '+', (p) => p.a === 1 || p.b === 1),
  trick('add 2 (skip-count)', 'a + 2 = a then next-next', '+', (p) => p.a === 2 || p.b === 2),
  trick('add 10 (place value)', 'a + 10 increments the tens digit', '+', (p) => p.a === 10 || p.b === 10),
  trick('add 9/11 as 10±1', 'a + 9 = a + 10 − 1; a + 11 = a + 10 + 1', '+', (p) => [9, 11].includes(p.a) || [9, 11].includes(p.b)),
  trick('doubles', 'a + a — memorized as a fact family', '+', (p) => p.a === p.b),
  trick('near doubles', 'a + (a+1) = 2a + 1', '+', (p) => Math.abs(p.a - p.b) === 1),
  trick('make ten', 'a + b where a + b = 10 (complement pairs)', '+', (p) => p.a + p.b === 10 && p.a > 0 && p.b > 0),
  trick('bridge through 10', 'Split one number so the other reaches 10 first, e.g. 8 + 5 = 8 + 2 + 3', '+', (p) => p.a >= 1 && p.a <= 9 && p.b >= 1 && p.b <= 9 && p.a + p.b > 10 && ![1, 2].includes(p.a) && ![1, 2].includes(p.b)),
  trick('add 12 as 10 + 2', 'a + 12 = a + 10 + 2', '+', (p) => p.a === 12 || p.b === 12),
  trick('partition small (no carry)', 'For two small numbers totaling at most 10, split one operand if useful', '+', (p) => p.a >= 1 && p.a <= 9 && p.b >= 1 && p.b <= 9 && p.a + p.b <= 10),
  trick('add near 100', 'a + 99 = a + 100 − 1, etc.', '+', (p) => near(p.a, 100) || near(p.b, 100)),

  trick('subtract 0', 'a − 0 = a', '-', (p) => p.b === 0),
  trick('subtract self', 'a − a = 0', '-', (p) => p.a === p.b),
  trick('subtract 1 (count down)', 'a − 1 is the previous number', '-', (p) => p.b === 1),
  trick('subtract 10', 'a − 10 decrements the tens digit', '-', (p) => p.b === 10),
  trick('subtract 9/11 as 10±1', 'a − 9 = a − 10 + 1; a − 11 = a − 10 − 1', '-', (p) => [9, 11].includes(p.b)),
  trick('subtract near 100', 'a − 99 = a − 100 + 1', '-', (p) => near(p.b, 100)),
  trick('count up (small gap)', 'When the numbers are close, count up from the smaller number', '-', (p) => p.a - p.b > 0 && p.a - p.b <= 3),
  trick('inverse of a double', '2a − a = a', '-', (p) => p.a === 2 * p.b && p.b > 0),
  trick('inverse of an addition fact', 'Recall the matching addition: find what must be added to b to make a', '-', (p) => p.b >= 0 && p.b <= 12 && p.a - p.b >= 0 && p.a - p.b <= 12),
  trick('subtract from a teen (split)', '13 − 5 = (10 − 5) + 3; split the teen into 10 + ones', '-', (p) => p.a >= 11 && p.a <= 19 && p.b >= 1 && p.b <= 9 && p.a - p.b >= 0),
  trick('subtract from 20', '20 − b: complement to 10 plus 10', '-', (p) => p.a === 20 && p.b >= 1 && p.b <= 19),

  trick('multiply by 0', 'a × 0 = 0', '*', (p) => p.a === 0 || p.b === 0),
  trick('multiply by 1 (identity)', 'a × 1 = a', '*', (p) => p.a === 1 || p.b === 1),
  trick('multiply by 2 (double)', 'a × 2 = a + a', '*', (p) => p.a === 2 || p.b === 2),
  trick('multiply by 5', 'a × 5 = a × 10 ÷ 2', '*', (p) => p.a === 5 || p.b === 5),
  trick('multiply by 10 (append zero)', 'a × 10 = a with a zero appended', '*', (p) => p.a === 10 || p.b === 10),
  trick('multiply by power of 10', 'a × 10ᵏ appends k zeros', '*', (p) => (powerOfTen(p.a) && p.a > 1) || (powerOfTen(p.b) && p.b > 1)),
  trick('multiply by 11 (small)', 'For 1–9: a × 11 repeats the digit', '*', (p) => (p.a === 11 && p.b >= 1 && p.b <= 9) || (p.b === 11 && p.a >= 1 && p.a <= 9)),
  trick('multiply by 11 (split-and-sum)', 'a × 11 = a × 10 + a', '*', (p) => p.a === 11 || p.b === 11),
  trick('multiply by 9 (10×a − a)', 'a × 9 = a × 10 − a', '*', (p) => p.a === 9 || p.b === 9),
  trick('square', 'a × a — memorize the squares from 1 to 12', '*', (p) => p.a === p.b),
  trick('double-and-half', 'Double one factor and halve the even factor', '*', (p) => ((p.a % 2 === 0 && p.a >= 4) || (p.b % 2 === 0 && p.b >= 4)) && ![0, 1, 2, 5, 10, 11].includes(p.a) && ![0, 1, 2, 5, 10, 11].includes(p.b)),
  trick('multiply by 4 (double twice)', 'a × 4 = (a × 2) × 2', '*', (p) => p.a === 4 || p.b === 4),
  trick('distributive split', 'Split a factor: 3 × 7 = 3 × 6 + 3', '*', (p) => p.a >= 3 && p.a <= 9 && p.b >= 3 && p.b <= 9 && p.a !== 5 && p.b !== 5),
  trick('multiply near 10', 'Multiply by 9 or 11 using ×10 ± one group', '*', (p) => [9, 11].includes(p.a) || [9, 11].includes(p.b)),

  trick('divide by 1', 'a ÷ 1 = a', '/', (p) => p.b === 1),
  trick('divide by self', 'a ÷ a = 1', '/', (p) => p.a === p.b && p.b !== 0),
  trick('divide by 2 (halve)', 'a ÷ 2 — halve', '/', (p) => p.b === 2),
  trick('divide by 5', 'a ÷ 5 = a × 2 ÷ 10', '/', (p) => p.b === 5),
  trick('divide by 10', 'a ÷ 10 — strip a zero', '/', (p) => p.b === 10),
  trick('inverse multiplication fact', 'Recall the matching multiplication fact', '/', (p) => p.b !== 0 && p.a % p.b === 0),
];

export const TRICKS_BY_NAME = new Map(TRICKS.map((item) => [item.name, item]));
