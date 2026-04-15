'use client';

import Link from 'next/link';

export const getNavItems = (pathname: string, onClick?: () => void) => {
  const navItem = (href: string, label: string) => (
    <Link
      key={href}
      href={href}
      onClick={onClick}
      className={`block px-4 py-2.5 rounded-lg text-sm transition ${
        pathname === href ? 'bg-black text-white font-medium' : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      {label}
    </Link>
  );

  return [
    navItem('/dashboard', 'Overview'),
    navItem('/dashboard/ai_service', 'AI Tutor'),
    navItem('/dashboard/analytics', 'Analytics'),
    navItem('/dashboard/mocktest/results', 'Mock Tests'),
    navItem('/dashboard/roadmap', 'Roadmap'),
    navItem('/dashboard/roadmaps', 'My Roadmaps'),
  ];
};
