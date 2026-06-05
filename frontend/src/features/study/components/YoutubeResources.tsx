'use client';

import Image from 'next/image';

type YouTubeVideo = {
  title?: string;
  video_id: string;
  thumbnail?: string;
};

type Props = {
  topicName: string;
  youtubeLinks: YouTubeVideo[] | string[];
};

export default function YouTubeResources({ topicName, youtubeLinks }: Readonly<Props>) {
  if (!youtubeLinks || youtubeLinks.length === 0) return null;

  return (
    <div>
      <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">Recommended Videos</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-6">
        {youtubeLinks.map((link, idx) => {
          const videoId = typeof link === 'string' ? extractYouTubeId(link) : link.video_id;
          const url = typeof link === 'string' ? link : `https://www.youtube.com/watch?v=${link.video_id}`;
          const title = `Learn ${topicName}`;

          return (
            <div
              key={videoId || idx}
              className="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition"
            >
              <a href={url} target="_blank" rel="noopener noreferrer">
                <Image
                  src={`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`}
                  alt="video thumbnail"
                  width={320}
                  height={180}
                  className="w-full h-40 sm:h-48 object-cover"
                />
              </a>

              <div className="p-3 sm:p-4">
                <p className="text-xs sm:text-sm font-medium">Learn {title}</p>
                <p className="text-xs text-gray-500 mt-1">Click to watch on YouTube</p>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mt-2 sm:mt-3 text-blue-600 text-xs sm:text-sm font-medium"
                >
                  Watch
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function extractYouTubeId(url: string) {
  const regex = /v=([^&]+)/;
  const match = regex.exec(url);
  return match ? match[1] : '';
}
