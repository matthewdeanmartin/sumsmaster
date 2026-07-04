import { Plan } from './models';

export const PLANS: readonly Plan[] = [
  { id: 'everything', name: 'Everything', description: 'All tricks across addition, subtraction, multiplication and division.', operations: ['+', '-', '*', '/'] },
  { id: 'addition-foundations', name: 'Addition Foundations', description: 'Counting on, doubles, make-ten and compensation strategies.', operations: ['+'] },
  { id: 'subtraction-strategies', name: 'Subtraction Strategies', description: 'Counting up, teen splits and near-ten compensation.', operations: ['-'] },
  { id: 'times-tables', name: 'Times-Table Tricks', description: 'The 12×12 grid through doubling, ×5, ×9, ×10, ×11 and splits.', operations: ['*'] },
  { id: 'division-basics', name: 'Division Basics', description: 'Halving, ÷5, ÷10 and inverse multiplication facts.', operations: ['/'] },
];

export function getPlan(planId: string): Plan {
  return PLANS.find((plan) => plan.id === planId) ?? PLANS[0];
}
