'use client';

import Providers from '@/components/layout/Providers';
import Navbar from '@/components/layout/Navbar';
import Drawer from '@/components/layout/Drawer';
import './globals.css';
import { useState } from 'react';

export default function RootLayout({ children }: { readonly children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <html lang="en">
      <body>
        <Providers>
          <Navbar openDrawer={() => setIsOpen(true)} />

          <Drawer isOpen={isOpen} close={() => setIsOpen(false)} />

          {children}
        </Providers>
      </body>
    </html>
  );
}
