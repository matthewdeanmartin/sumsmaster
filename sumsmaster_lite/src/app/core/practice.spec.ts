import { Profile, answerFor } from './models';
import { coverageReport } from './coverage';
import { isValidSession, startSession, submitAnswer } from './practice';

function profile(): Profile {
  return { version: 1, name: 'Maya', planId: 'times-tables', createdAt: new Date().toISOString(), progress: {}, session: null };
}

describe('practice engine', () => {
  it('builds a resumable ten-question queue for the selected plan', () => {
    const learner = profile();
    startSession(learner);
    expect(learner.session?.queue).toHaveLength(10);
    expect(learner.session?.queue.every((item) => item.op === '*')).toBe(true);
    expect(isValidSession(learner)).toBe(true);
  });

  it('grades an answer and updates trick progress', () => {
    const learner = profile();
    startSession(learner, 2);
    const question = learner.session!.queue[0];
    const result = submitAnswer(learner, answerFor(question));
    expect(result.correct).toBe(true);
    expect(learner.progress[question.trickName]).toMatchObject({ attempts: 1, correct: 1, streak: 1 });
    expect(learner.session?.answered).toBe(1);
  });

  it('analyzes the same 713-fact domain used by the desktop app', () => {
    const reports = coverageReport();
    expect(reports.reduce((sum, report) => sum + report.total, 0)).toBe(713);
    expect(reports.every((report) => report.covered > 0)).toBe(true);
  });
});
