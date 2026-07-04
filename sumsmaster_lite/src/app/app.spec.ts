import { TestBed } from '@angular/core/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({ imports: [App] }).compileComponents();
  });

  it('offers single-learner setup when local storage is empty', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    expect((fixture.nativeElement as HTMLElement).querySelector('h1')?.textContent).toContain('Build number sense');
  });

  it('creates and persists one learner', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    app.setupName = 'Maya';
    app.setupPlanId = 'times-tables';
    app.createProfile();
    expect(app.profile?.name).toBe('Maya');
    expect(app.profile?.planId).toBe('times-tables');
    expect(JSON.parse(localStorage.getItem('sumsmaster-lite.profile.v1')!).name).toBe('Maya');
  });
});
