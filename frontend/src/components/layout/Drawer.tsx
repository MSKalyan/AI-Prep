'use client';

import Link from 'next/link';
import { getNavItems } from './navItems';
import { useAuth } from '@/features/auth';
import { usePathname } from 'next/navigation';

export default function Drawer({ isOpen, close }: { readonly isOpen: boolean; readonly close: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth(); // ✅ SAFE HERE

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <button
          type="button"
          className="fixed inset-0 bg-black/40 z-40"
          onClick={close}
          onKeyDown={(e) => {
            if (e.key === 'Escape') close();
          }}
          aria-label="Close menu"
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed top-0 left-0 h-full w-64 bg-white z-50 transform transition-transform duration-300 
        ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:hidden`}
      >
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-sm font-semibold">Menu</h2>
          <button onClick={close}>✕</button>
        </div>

        <nav className="p-4 space-y-2">
          {getNavItems(pathname, close)}

          <hr />

          {user && (
            <>
              <Link
                href="/profile"
                onClick={close}
                className="block px-4 py-2 text-sm text-gray-600"
              >
                Profile
              </Link>

              <button
                onClick={() => {
                  logout();
                  close();
                }}
                className="block w-full text-left px-4 py-2 text-sm text-red-500"
              >
                Logout
              </button>
            </>
          )}
        </nav>
      </div>
    </>
  );
}
