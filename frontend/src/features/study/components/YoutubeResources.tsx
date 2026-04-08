"use client";

type Props = {
  topicName: string;
  youtubeLinks: string[];
};

export default function YouTubeResources({
  topicName,
  youtubeLinks,
}: Props) {
  if (!youtubeLinks || youtubeLinks.length === 0) return null;

  return (
    <div>
      <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">
        🎥 Recommended Videos
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-6">
        {youtubeLinks.map((link, index) => {
          const videoId = extractYouTubeId(link);

          return (
            <div
              key={index}
              className="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition"
            >
              {/* Thumbnail */}
              <a href={link} target="_blank" rel="noopener noreferrer">
                <img
                  src={`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`}
                  alt="video thumbnail"
                  className="w-full h-40 sm:h-48 object-cover"
                />
              </a>

              {/* Content */}
              <div className="p-3 sm:p-4">
                <p className="text-xs sm:text-sm font-medium">
                  Learn {topicName}
                </p>

                <p className="text-xs text-gray-500 mt-1">
                  Click to watch on YouTube
                </p>

                <a
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-2 sm:mt-3 text-blue-600 text-xs sm:text-sm font-medium"
                >
                  Watch →
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ================= HELPER ================= */

function extractYouTubeId(url: string) {
  const match = url.match(/v=([^&]+)/);
  return match ? match[1] : "";
}