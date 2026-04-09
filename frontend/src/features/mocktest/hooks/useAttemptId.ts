"use client";

import { useParams } from "next/navigation";

export function useAttemptId() {
  const params = useParams();

  const rawId = params?.id;

  const attemptId =
    typeof rawId === "string"
      ? Number(rawId)
      : Array.isArray(rawId)
      ? Number(rawId[0])
      : null;

  return attemptId;
}
