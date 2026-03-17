import DocumentUpload from "@/features/ai/components/DocumentUpload";
import AskAIChat from "@/features/ai/components/AskAIChat";

export default function AIPage() {
  return (
    <div className="p-6 space-y-6">
      <DocumentUpload />
      <AskAIChat />
    </div>
  );
}