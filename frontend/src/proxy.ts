import { NextResponse } from 'next/server';

const PROTECTED_PATHS = ['/dashboard'];

import type { NextRequest } from 'next/server';

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PATHS.some((path) => pathname.startsWith(path));

  if (isProtected) {
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
