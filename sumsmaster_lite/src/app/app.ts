import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CoverageResult, coverageReport } from './core/coverage';
import { MASTERY_STREAK, Operation, Profile, Trick, displayOperator, operationLabel } from './core/models';
import { PLANS, getPlan } from './core/plans';
import { isValidSession, startSession, submitAnswer } from './core/practice';
import { StorageService } from './core/storage.service';
import { TRICKS } from './core/tricks';

type Screen = 'dashboard' | 'practice' | 'tricks' | 'coverage' | 'settings';

interface Feedback {
  correct: boolean;
  expected: number;
  trick: Trick;
}

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  readonly plans = PLANS;
  readonly masteryStreak = MASTERY_STREAK;
  readonly operationGroups = (['+', '-', '*', '/'] as const).map((operation) => ({
    operation,
    label: operationLabel(operation),
    tricks: TRICKS.filter((item) => item.operation === operation),
  }));

  profile: Profile | null;
  screen: Screen = 'dashboard';
  setupName = '';
  setupPlanId = 'everything';
  editName = '';
  editPlanId = 'everything';
  answerInput = '';
  answerError = '';
  feedback: Feedback | null = null;
  completedScore: { correct: number; total: number } | null = null;
  coverage: CoverageResult[] | null = null;

  constructor(private readonly storage: StorageService) {
    this.profile = storage.load();
    if (this.profile && !isValidSession(this.profile)) {
      this.profile.session = null;
      this.storage.save(this.profile);
    }
    this.syncSettingsForm();
  }

  get plan() {
    return getPlan(this.profile?.planId ?? this.setupPlanId);
  }

  get planTricks(): readonly Trick[] {
    return TRICKS.filter((item) => this.plan.operations.includes(item.operation));
  }

  get masteredCount(): number {
    if (!this.profile) return 0;
    return this.planTricks.filter((item) => (this.profile!.progress[item.name]?.streak ?? 0) >= MASTERY_STREAK).length;
  }

  get masteryPercentage(): number {
    return this.planTricks.length ? 100 * this.masteredCount / this.planTricks.length : 0;
  }

  get currentQuestion() {
    return this.profile?.session?.queue[0] ?? null;
  }

  get questionNumber(): number {
    return (this.profile?.session?.answered ?? 0) + 1;
  }

  get totalAttempts(): number {
    return Object.values(this.profile?.progress ?? {}).reduce((sum, item) => sum + item.attempts, 0);
  }

  get totalCorrect(): number {
    return Object.values(this.profile?.progress ?? {}).reduce((sum, item) => sum + item.correct, 0);
  }

  createProfile(): void {
    if (!this.setupName.trim()) return;
    this.profile = this.storage.create(this.setupName, this.setupPlanId);
    this.syncSettingsForm();
    this.screen = 'dashboard';
  }

  navigate(screen: Screen): void {
    this.screen = screen;
    if (screen === 'coverage' && !this.coverage) this.coverage = coverageReport();
    if (screen === 'settings') this.syncSettingsForm();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  beginPractice(): void {
    if (!this.profile) return;
    if (this.profile.session?.queue.length && !window.confirm('Start over and replace the paused session?')) return;
    startSession(this.profile);
    this.storage.save(this.profile);
    this.resetPracticeUi();
    this.screen = 'practice';
  }

  resumePractice(): void {
    if (!this.profile?.session?.queue.length) return;
    this.resetPracticeUi();
    this.screen = 'practice';
  }

  checkAnswer(): void {
    if (!this.profile || !this.currentQuestion || this.feedback) return;
    if (!/^-?\d+$/.test(this.answerInput.trim())) {
      this.answerError = 'Enter a whole number.';
      return;
    }
    const finishingSession = this.profile.session!;
    this.feedback = submitAnswer(this.profile, Number(this.answerInput));
    this.answerError = '';
    if (!this.profile.session) {
      this.completedScore = { correct: finishingSession.correct, total: finishingSession.total };
    }
    this.storage.save(this.profile);
  }

  nextQuestion(): void {
    this.feedback = null;
    this.answerInput = '';
    this.answerError = '';
  }

  pausePractice(): void {
    this.resetPracticeUi();
    this.navigate('dashboard');
  }

  abandonPractice(): void {
    if (!this.profile || !window.confirm('End this session? Progress already earned will stay saved.')) return;
    this.profile.session = null;
    this.storage.save(this.profile);
    this.resetPracticeUi();
    this.navigate('dashboard');
  }

  saveSettings(): void {
    if (!this.profile || !this.editName.trim()) return;
    const planChanged = this.profile.planId !== this.editPlanId;
    if (planChanged && this.profile.session && !window.confirm('Changing plan will discard the paused session. Continue?')) return;
    this.profile.name = this.editName.trim();
    this.profile.planId = getPlan(this.editPlanId).id;
    if (planChanged) this.profile.session = null;
    this.storage.save(this.profile);
    this.navigate('dashboard');
  }

  resetLearner(): void {
    if (!window.confirm('Erase this learner and all practice progress from this browser? This cannot be undone.')) return;
    this.storage.clear();
    this.profile = null;
    this.setupName = '';
    this.setupPlanId = 'everything';
    this.screen = 'dashboard';
  }

  progressFor(trick: Trick) {
    return this.profile?.progress[trick.name] ?? null;
  }

  accuracyFor(trick: Trick): string {
    const progress = this.progressFor(trick);
    return progress?.attempts ? `${Math.round(100 * progress.correct / progress.attempts)}%` : '—';
  }

  isMastered(trick: Trick): boolean {
    return (this.progressFor(trick)?.streak ?? 0) >= MASTERY_STREAK;
  }

  symbol(operation: Operation): string {
    return displayOperator(operation);
  }

  coverageTotal(): { covered: number; total: number; percentage: number } {
    const total = (this.coverage ?? []).reduce((sum, item) => sum + item.total, 0);
    const covered = (this.coverage ?? []).reduce((sum, item) => sum + item.covered, 0);
    return { covered, total, percentage: total ? 100 * covered / total : 0 };
  }

  private resetPracticeUi(): void {
    this.feedback = null;
    this.completedScore = null;
    this.answerInput = '';
    this.answerError = '';
  }

  private syncSettingsForm(): void {
    this.editName = this.profile?.name ?? '';
    this.editPlanId = this.profile?.planId ?? 'everything';
  }
}
