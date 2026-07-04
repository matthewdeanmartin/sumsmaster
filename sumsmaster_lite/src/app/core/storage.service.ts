import { Injectable } from '@angular/core';
import { Profile, TrickProgress } from './models';
import { getPlan } from './plans';

const STORAGE_KEY = 'sumsmaster-lite.profile.v1';

@Injectable({ providedIn: 'root' })
export class StorageService {
  load(): Profile | null {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const value = JSON.parse(raw) as Partial<Profile>;
      if (value.version !== 1 || typeof value.name !== 'string') return null;
      return {
        version: 1,
        name: value.name,
        planId: getPlan(value.planId ?? '').id,
        createdAt: value.createdAt ?? new Date().toISOString(),
        progress: this.validProgress(value.progress),
        session: value.session ?? null,
      };
    } catch {
      return null;
    }
  }

  save(profile: Profile): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
  }

  create(name: string, planId: string): Profile {
    const profile: Profile = {
      version: 1,
      name: name.trim() || 'Learner',
      planId: getPlan(planId).id,
      createdAt: new Date().toISOString(),
      progress: {},
      session: null,
    };
    this.save(profile);
    return profile;
  }

  clear(): void {
    localStorage.removeItem(STORAGE_KEY);
  }

  private validProgress(value: unknown): Record<string, TrickProgress> {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
    const output: Record<string, TrickProgress> = {};
    for (const [name, progress] of Object.entries(value)) {
      if (!progress || typeof progress !== 'object') continue;
      const item = progress as Partial<TrickProgress>;
      output[name] = {
        attempts: Number(item.attempts) || 0,
        correct: Number(item.correct) || 0,
        streak: Number(item.streak) || 0,
        lastPracticed: typeof item.lastPracticed === 'string' ? item.lastPracticed : null,
      };
    }
    return output;
  }
}
