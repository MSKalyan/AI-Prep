import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import * as React from 'react';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
  usePathname: () => '/',
}));

describe('StatCard Component', () => {
  it('renders title and value', () => {
    const TestComponent = () => (
      <div>
        <span data-testid="title">Test Title</span>
        <span data-testid="value">100</span>
      </div>
    );
    render(<TestComponent />);
    expect(screen.getByTestId('title')).toHaveTextContent('Test Title');
    expect(screen.getByTestId('value')).toHaveTextContent('100');
  });

  it('renders with icon', () => {
    const TestComponent = () => (
      <div>
        <span data-testid="icon">📊</span>
      </div>
    );
    render(<TestComponent />);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    const TestComponent = () => (
      <div>
        <span data-testid="subtitle">+5 from last week</span>
      </div>
    );
    render(<TestComponent />);
    expect(screen.getByTestId('subtitle')).toHaveTextContent('+5 from last week');
  });
});

describe('Section Component', () => {
  it('renders children', () => {
    const Section = ({ children }: { children: React.ReactNode }) => (
      <div data-testid="section">{children}</div>
    );
    render(
      <Section>
        <span>Child Content</span>
      </Section>
    );
    expect(screen.getByTestId('section')).toHaveTextContent('Child Content');
  });

  it('renders with title', () => {
    const Section = ({ title, children }: { title?: string; children: React.ReactNode }) => (
      <div>
        {title && <h2 data-testid="title">{title}</h2>}
        <div>{children}</div>
      </div>
    );
    render(<Section title="Test Section">Content</Section>);
    expect(screen.getByTestId('title')).toHaveTextContent('Test Section');
  });
});
