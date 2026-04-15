export default function StatCard({ title, value }: Readonly<{ title: string; value: string | number }>) {
  return (
    <div className="border border-gray-200 rounded-2xl p-4 sm:p-5 hover:shadow-md transition">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{title}</p>
      <h2 className="text-lg sm:text-2xl font-semibold mt-1">{value}</h2>
    </div>
  );
}
