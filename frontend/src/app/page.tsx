
"use client";

import { useRouter } from "next/navigation";

export default function HomeImproved() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-100 text-black">

      {/* HERO */}
      <section className="px-6 md:px-12 pt-24 pb-20 max-w-6xl mx-auto text-center">

        <p className="text-xs tracking-widest text-gray-400 mb-4">
          AI STUDY SYSTEM
        </p>

        <h1 className="text-4xl md:text-6xl xl:text-7xl font-bold leading-tight tracking-tight">
          Stop guessing.
          <br />
          <span className="text-gray-500">Start preparing right.</span>
        </h1>

        <p className="mt-6 text-gray-600 text-base md:text-lg max-w-2xl mx-auto">
          A performance-driven system that guides what to study, when to revise,
          and how to improve — using real data from your attempts.
        </p>

        <div className="mt-10 flex justify-center gap-4">
          <button
            onClick={() => router.push("/dashboard")}
            className="px-8 py-3 bg-black text-white rounded-full font-medium hover:scale-105 transition"
          >
            Enter Dashboard
          </button>

        </div>

      </section>

      {/* TRUST STRIP */}
      <section className="border-y py-6 text-center text-sm text-gray-500">
        Built for serious aspirants • Data-driven • Adaptive learning
      </section>

      {/* FEATURES */}
      <section className="px-6 md:px-12 py-20 max-w-6xl mx-auto">

        <div className="text-center mb-12">
          <h2 className="text-3xl font-semibold">Everything you need</h2>
          <p className="text-gray-500 mt-2">Designed for structured preparation</p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">

          {[
            { title: "Roadmap", desc: "Structured daily plan with clear topic coverage" },
            { title: "Revision", desc: "Automatically revisits weak areas" },
            { title: "Mock Tests", desc: "Real exam-like test environment" },
            { title: "Analytics", desc: "Accuracy, speed, and topic insights" },
            { title: "AI Explanations", desc: "Concise explanations for fast revision" },
            { title: "Focus System", desc: "Removes distractions and guides learning" }
          ].map((item, i) => (
            <div
              key={i}
              className="bg-white p-6 rounded-2xl shadow-sm hover:shadow-lg transition border"
            >
              <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
              <p className="text-sm text-gray-600">{item.desc}</p>
            </div>
          ))}

        </div>

      </section>

      {/* VALUE */}
      <section className="px-6 md:px-12 py-20 text-center max-w-4xl mx-auto">

        <h2 className="text-3xl md:text-4xl font-semibold leading-snug">
          Built for consistency, not motivation.
        </h2>

        <p className="mt-6 text-gray-600 text-base">
          The system adapts based on your performance and ensures you focus
          on what actually improves your score.
        </p>

      </section>

      {/* CTA */}
      <section className="px-6 md:px-12 py-20 text-center">

        <div className="bg-black text-white rounded-2xl p-10 max-w-3xl mx-auto">
          <h3 className="text-xl md:text-2xl font-semibold mb-4">
            Start your preparation today
          </h3>

          <button
            onClick={() => router.push("/dashboard")}
            className="px-6 py-3 bg-white text-black rounded-full font-medium hover:opacity-90 transition"
          >
            Go to Dashboard
          </button>
        </div>

      </section>

      {/* FOOTER */}
      <footer className="text-center text-xs text-gray-400 pb-6">
        © {new Date().getFullYear()} PrepAI
      </footer>

    </div>
  );
}