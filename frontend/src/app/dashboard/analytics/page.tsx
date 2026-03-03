export default function AnalyticsPage() {
  return (
    <div className="max-w-5xl">

      <h1 className="text-3xl font-bold mb-6">
        Analytics
      </h1>

      <p className="text-gray-600 mb-8">
        View your performance insights, exam progress, and study statistics.
      </p>

      {/* Analytics Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        <div className="bg-white shadow-md rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-2">Accuracy</h2>
          <p className="text-2xl font-bold">--%</p>
        </div>

        <div className="bg-white shadow-md rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-2">Tests Completed</h2>
          <p className="text-2xl font-bold">--</p>
        </div>

        <div className="bg-white shadow-md rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-2">Study Hours</h2>
          <p className="text-2xl font-bold">-- hrs</p>
        </div>

      </div>

    </div>
  );
}