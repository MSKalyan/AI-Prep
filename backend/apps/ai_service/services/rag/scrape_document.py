from ...models import Document
from .web_scraper import scrape_webpage


def scrape_and_store_document(url, subject, exam_type, topic=""):

    text = scrape_webpage(url)

    document = Document.objects.create(
        title=url,
        content=text,
        subject=subject,
        topic=topic,
        exam_type=exam_type,
        source_url=url,
        source_type="scraped",
        document_type="article",
        processed=False
    )

    return document