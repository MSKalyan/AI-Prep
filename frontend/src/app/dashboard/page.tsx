import Link from "next/link";

const services = [
  {
    name: "AI Service",
    description: "Ask AI questions powered by RAG and conversation history.",
    href: "/dashboard/ai_service",
  },
  {
    name: "Analytics",
    description: "View performance metrics and exam insights.",
    href: "/dashboard/analytics",
  },
  {
    name: "Mock Tests",
    description: "Attempt mock exams and evaluate your performance.",
    href: "/dashboard/mocktest",
  },
  {
    name: "Roadmap",
    description: "Generate and track your personalized exam roadmap.",
    href: "/dashboard/roadmap",
  },
];

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        
        <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {services.map((service) => (
            <Link
              key={service.name}
              href={service.href}
              className="bg-white shadow-md rounded-xl p-6 hover:shadow-lg transition"
            >
              <h2 className="text-xl font-semibold mb-2">
                {service.name}
              </h2>
              <p className="text-gray-600 text-sm">
                {service.description}
              </p>
            </Link>
          ))}
        </div>

      </div>
    </div>
  );
}