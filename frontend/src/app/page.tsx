"use client";

import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white text-black">

      {/* HERO */}
      <section className="px-4 sm:px-6 md:px-12 pt-16 sm:pt-24 md:pt-28 pb-16 sm:pb-20 md:pb-24 max-w-6xl mx-auto text-center">

        <p className="text-xs uppercase tracking-widest text-gray-400 mb-3 sm:mb-4">
          AI STUDY SYSTEM
        </p>

        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight tracking-tight">
          Stop guessing.
          <br />
          <span className="italic">Start preparing right.</span>
        </h1>

        <p className="mt-4 sm:mt-6 text-gray-600 text-sm sm:text-base md:text-lg max-w-2xl mx-auto">
          A structured system that tells you what to study, when to revise,
          and how to improve — based on your performance.
        </p>

        <div className="mt-8 sm:mt-10">
          <button
            onClick={() => router.push("/dashboard")}
            className="px-6 sm:px-8 py-2 sm:py-3 bg-black text-white rounded-full text-xs sm:text-sm font-semibold hover:scale-105 transition"
          >
            Enter Dashboard
          </button>
        </div>

      </section>

      {/* DIVIDER */}
      <div className="border-t"></div>

      {/* FEATURES GRID */}
      <section className="px-4 sm:px-6 md:px-12 py-16 sm:py-20 md:py-24 max-w-6xl mx-auto">

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 md:gap-10">

          {[
            {
              title: "Roadmap",
              desc: "Every topic mapped with time allocation. No randomness."
            },
            {
              title: "Revision",
              desc: "Weak areas are automatically pushed back into your flow."
            },
            {
              title: "Testing",
              desc: "Topic-based tests that reflect real exam pressure."
            },
            {
              title: "Analytics",
              desc: "Track accuracy, speed, and consistency clearly."
            },
            {
              title: "Explanations",
              desc: "Short, structured explanations for fast recall."
            },
            {
              title: "Focus",
              desc: "Removes noise. Keeps you on what actually matters."
            }
          ].map((item, i) => (
            <div
              key={i}
              className="group border p-4 sm:p-6 rounded-xl hover:bg-black hover:text-white transition duration-300"
            >
              <h3 className="font-semibold text-base sm:text-lg mb-2">
                {item.title}
              </h3>
              <p className="text-xs sm:text-sm text-gray-600 group-hover:text-gray-300">
                {item.desc}
              </p>
            </div>
          ))}

        </div>

      </section>

      {/* VALUE SECTION */}
      <section className="px-4 sm:px-6 md:px-12 py-16 sm:py-20 md:py-24 border-t text-center max-w-4xl mx-auto">

        <h2 className="text-2xl sm:text-3xl md:text-4xl font-semibold leading-snug">
          Built for people who are serious about cracking exams.
        </h2>

        <p className="mt-4 sm:mt-6 text-gray-600 text-sm sm:text-base">
          Not just tests.
          <br />
          A system that adapts to how you perform.
        </p>

      </section>

      {/* FINAL CTA */}
      <section className="px-4 sm:px-6 md:px-12 py-16 sm:py-20 md:py-24 text-center">

        <div className="inline-block border px-6 sm:px-10 py-8 sm:py-10 rounded-2xl">

          <h3 className="text-lg sm:text-xl font-semibold mb-4">
            Ready to start?
          </h3>

          <button
            onClick={() => router.push("/dashboard")}
            className="px-5 sm:px-6 py-2 sm:py-3 bg-black text-white rounded-full text-xs sm:text-sm font-semibold hover:opacity-90 transition"
          >
            Go to Dashboard
          </button>

        </div>

      </section>

      {/* FOOTER */}
      <footer className="text-center text-xs text-gray-400 pb-4 sm:pb-6 px-4">
        © {new Date().getFullYear()} PrepAI
      </footer>

    </div>
  );
}