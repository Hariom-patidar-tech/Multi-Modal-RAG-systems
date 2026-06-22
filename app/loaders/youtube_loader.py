from youtube_transcript_api import YouTubeTranscriptApi
from app.core.logger import logger
import re


class YouTubeLoader:

    def _extract_video_id(self, url: str) -> str:
        pattern = r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/|&v=)([a-zA-Z0-9_-]{11})'

        match = re.search(pattern, url)

        if match:
            return match.group(1)

        if len(url.strip()) == 11:
            return url.strip()

        raise ValueError("Invalid YouTube URL")

    def load(self, url: str):

        try:
            video_id = self._extract_video_id(url)

            logger.info(f"Video ID: {video_id}")

            api = YouTubeTranscriptApi()

            transcript = api.fetch(
            video_id,
             languages=["hi", "en"]
            )

            chunks = []

            for item in transcript:
                if hasattr(item, "text"):
                    chunks.append(item.text)
                elif isinstance(item, dict):
                    chunks.append(item.get("text", ""))

            full_text = " ".join(chunks)

            logger.info(
                f"Transcript extracted successfully. Characters: {len(full_text)}"
            )

            return [
                {
                    "text": full_text,
                    "metadata": {
                        "source": f"youtube_{video_id}",
                        "type": "youtube"
                    }
                }
            ]

        except Exception as e:
            logger.exception("YouTube Loader Failed")

            raise Exception(
                f"YouTube transcript extraction failed: {str(e)}"
            )