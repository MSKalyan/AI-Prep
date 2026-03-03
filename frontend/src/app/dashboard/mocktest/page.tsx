"use client";

import { useRouter } from "next/navigation";
import { useCreateMockTest } from "@/features/mocktest/hooks/useMockTest";
import CreateMockTestForm from "@/features/mocktest/components/CreateMockTestForm";

export default function MockTestPage() {

  const router = useRouter();
  const { mutateAsync } = useCreateMockTest();

  const handleCreate = async(payload:any)=>{

    const res = await mutateAsync(payload);

    const testId = res.mock_test.id;
    const attemptId = res.attempt.id;

    router.push(
      `/dashboard/mocktest/${testId}?attempt=${attemptId}`
    );
  };

  return (
    <div className="p-6">
      <CreateMockTestForm createTest={handleCreate}/>
    </div>
  );
}