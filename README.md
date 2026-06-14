# astathasa-rahasyam-book

Local searchable web reader for the scanned Tamil book `Astathasa Rahasyam Book.pdf`.

## Open the reader

```sh
npm run serve
```

Then open `http://localhost:5173`.

## Regenerate the digitized data

```sh
npm run extract
```

The extractor renders scanned page images into `public/pages/`, runs Tamil OCR with Tesseract into `data/ocr/`, and writes:

- `data/book.json`: page metadata, OCR text, and page image paths
- `data/search-index.json`: inverted token index for fast search

Useful OCR settings:

```sh
OCR_CONCURRENCY=4 RENDER_DPI=190 OCR_PSM=6 npm run extract
FORCE_OCR=1 npm run extract
```

The existing `docs/` reader and Python helper scripts remain in the repository.
