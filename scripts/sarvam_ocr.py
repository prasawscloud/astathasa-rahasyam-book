"""
Full PDF → Tamil markdown using Sarvam AI Document Intelligence.
Splits into batches to stay under the 200 MB per-job limit.
"""

import os, time, sys, requests, fitz, zipfile, io, re
from sarvamai import SarvamAI, DocDigitizationJobParametersParams

import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

API_KEY   = _os.environ.get("SARVAM_API_KEY", "")
PDF_PATH  = _os.path.join(_ROOT, "Astathasa Rahasyam Book.pdf")
OUT_DIR   = _os.path.join(_ROOT, "sarvam_output")
BATCH_SIZE = 10    # Sarvam API allows max 10 pages per job

os.makedirs(OUT_DIR, exist_ok=True)
client = SarvamAI(api_subscription_key=API_KEY)
di     = client.document_intelligence

src        = fitz.open(PDF_PATH)
total_pages = len(src)
print(f"PDF has {total_pages} pages. Processing in batches of {BATCH_SIZE}.")

# ── Figure out batches ────────────────────────────────────────────────────────
batches = []
for start in range(0, total_pages, BATCH_SIZE):
    end = min(start + BATCH_SIZE - 1, total_pages - 1)
    batches.append((start, end))
print(f"Batches: {len(batches)}  ({[f'{s+1}-{e+1}' for s,e in batches]})\n")

def run_batch(start_page, end_page, batch_num, retries=3):
    """Process one batch with retries on network errors."""
    subset_path = os.path.join(OUT_DIR, f"batch_{batch_num:02d}_p{start_page+1}-{end_page+1}.pdf")
    subset_name = os.path.basename(subset_path)

    if not os.path.exists(subset_path):
        dst = fitz.open()
        dst.insert_pdf(src, from_page=start_page, to_page=end_page)
        dst.save(subset_path)
        dst.close()
    size_mb = os.path.getsize(subset_path) / 1024 / 1024
    print(f"  Batch {batch_num}: pages {start_page+1}–{end_page+1}  ({size_mb:.1f} MB)")

    for attempt in range(1, retries + 1):
        try:
            # Initialise job
            init = di.initialise(job_parameters=DocDigitizationJobParametersParams(
                language="ta-IN", output_format="md"))
            job_id = init.job_id

            # Get upload URL
            link_resp  = di.get_upload_links(job_id=job_id, files=[subset_name])
            upload_url = link_resp.upload_urls[subset_name].file_url

            # Upload
            with open(subset_path, "rb") as f:
                r = requests.put(upload_url, data=f, headers={"Content-Type": "application/pdf",
                                                               "x-ms-blob-type": "BlockBlob"})
            if r.status_code not in (200, 201, 204):
                raise RuntimeError(f"Upload failed HTTP {r.status_code}: {r.text}")

            # Start
            di.start(job_id=job_id)

            # Poll
            while True:
                status = di.get_status(job_id)
                state  = str(status.job_state)
                if state.lower() in ("completed", "failed", "error"):
                    break
                time.sleep(6)

            if state.lower() != "completed":
                raise RuntimeError(f"Job {job_id} failed: {status}")

            # Download zip
            dl_resp = di.get_download_links(job_id)
            zip_url = list(dl_resp.download_urls.values())[0].file_url
            r       = requests.get(zip_url)

            with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                for name in zf.namelist():
                    if name.endswith(".md"):
                        return zf.read(name).decode("utf-8")
            return ""

        except Exception as e:
            print(f"  Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                print(f"  Retrying in 10s...")
                time.sleep(10)
            else:
                raise

# ── Process all batches (resumes from last completed batch) ───────────────────
all_parts = []
for i, (start, end) in enumerate(batches, 1):
    cache_file = os.path.join(OUT_DIR, f"batch_{i:02d}_result.md")
    if os.path.exists(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            md = f.read()
        print(f"Batch {i}/{len(batches)}: pages {start+1}–{end+1} — loaded from cache ({len(md):,} chars)")
    else:
        print(f"\n── Batch {i}/{len(batches)}: pages {start+1}–{end+1} ──")
        md = run_batch(start, end, i)
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"  Done. Got {len(md):,} chars.")
    all_parts.append(md)

src.close()

# ── Combine and clean ─────────────────────────────────────────────────────────
combined = "\n\n---\n\n".join(all_parts)

# Strip base64 images
clean = re.sub(r'!\[Image\]\(data:image[^)]{0,500000}\)', '', combined, flags=re.DOTALL)
clean = re.sub(r'\n{3,}', '\n\n', clean).strip()

clean_out = os.path.join(OUT_DIR, "astathasa_rahasyam_tamil_full.md")
with open(clean_out, "w", encoding="utf-8") as f:
    f.write("# அஷ்டாதச ரஹஸ்யம்\n\n")
    f.write(clean)

print(f"\n{'='*50}")
print(f"Done! Full Tamil text saved to:")
print(f"  {clean_out}")
print(f"  Total chars: {len(clean):,}")
