import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('apiClient', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('apiClient module exists', async () => {
    const { apiClient } = await import('../lib/apiClient');
    expect(apiClient).toBeDefined();
    expect(typeof apiClient.get).toBe('function');
    expect(typeof apiClient.post).toBe('function');
  });
});

describe('authService', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('login function exists', async () => {
    const auth = await import('../features/auth/services/auth.service');
    expect(typeof auth.login).toBe('function');
  });

  it('register function exists', async () => {
    const auth = await import('../features/auth/services/auth.service');
    expect(typeof auth.register).toBe('function');
  });

  it('logout function exists', async () => {
    const auth = await import('../features/auth/services/auth.service');
    expect(typeof auth.logout).toBe('function');
  });

  it('getProfile function exists', async () => {
    const auth = await import('../features/auth/services/auth.service');
    expect(typeof auth.getProfile).toBe('function');
  });
});

describe('roadmapService', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('roadmap service exists', async () => {
    const service = await import('../features/roadmap/services/roadmap.service');
    expect(service).toBeDefined();
  });
});

describe('mocktestService', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('mocktest service exists', async () => {
    const service = await import('../features/mocktest/services/mocktest.service');
    expect(service).toBeDefined();
  });
});

describe('analyticsService', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('analytics service exists', async () => {
    const service = await import('../features/analytics/services/analytics.service');
    expect(service).toBeDefined();
  });
});

describe('aiService', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('ai service exists', async () => {
    const service = await import('../features/ai/services/ai.service');
    expect(service).toBeDefined();
  });
});

describe('studyService', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('study service exists', async () => {
    const service = await import('../features/study/services/study.service');
    expect(service).toBeDefined();
  });
});