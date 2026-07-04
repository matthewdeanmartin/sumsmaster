import { Operation, Problem, Trick, answerFor, displayOperator, operationLabel } from './models';
import { TRICKS } from './tricks';

export interface CoverageResult {
  operation: Operation;
  label: string;
  total: number;
  covered: number;
  percentage: number;
  uncovered: string[];
  hits: { trick: Trick; count: number }[];
}

export function coverageReport(): CoverageResult[] {
  const domains: [Operation, Problem[]][] = [
    ['+', grid('+', 0, 12)],
    ['-', subtractionGrid()],
    ['*', grid('*', 0, 12)],
    ['/', divisionGrid()],
  ];
  return domains.map(([operation, problems]) => {
    const relevant = TRICKS.filter((item) => item.operation === operation);
    const hitCounts = new Map(relevant.map((item) => [item.name, 0]));
    const uncovered: string[] = [];
    let covered = 0;
    for (const problem of problems) {
      const matches = relevant.filter((item) => item.matches(problem));
      if (matches.length) {
        covered++;
        matches.forEach((item) => hitCounts.set(item.name, (hitCounts.get(item.name) ?? 0) + 1));
      } else {
        uncovered.push(`${problem.a} ${displayOperator(problem.op)} ${problem.b} = ${answerFor(problem)}`);
      }
    }
    return {
      operation,
      label: operationLabel(operation),
      total: problems.length,
      covered,
      percentage: 100 * covered / problems.length,
      uncovered,
      hits: relevant.map((item) => ({ trick: item, count: hitCounts.get(item.name) ?? 0 })).sort((a, b) => b.count - a.count),
    };
  });
}

function grid(operation: Operation, low: number, high: number): Problem[] {
  const output: Problem[] = [];
  for (let a = low; a <= high; a++) for (let b = low; b <= high; b++) output.push({ a, b, op: operation });
  return output;
}

function subtractionGrid(): Problem[] {
  const output: Problem[] = [];
  for (let a = 0; a <= 20; a++) for (let b = 0; b <= a; b++) output.push({ a, b, op: '-' });
  return output;
}

function divisionGrid(): Problem[] {
  const output: Problem[] = [];
  for (let b = 1; b <= 12; b++) for (let quotient = 1; quotient <= 12; quotient++) output.push({ a: b * quotient, b, op: '/' });
  return output;
}
