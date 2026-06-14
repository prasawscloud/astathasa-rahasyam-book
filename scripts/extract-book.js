import { spawn } from "node:child_process";
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";

const projectRoot = process.cwd();
const pdfPath = process.argv[2] || "/Users/adhityaram/Downloads/Astathasa Rahasyam Book.pdf";
const renderDpi = Number(process.env.RENDER_DPI || 170);
const jpegQuality = Number(process.env.JPEG_QUALITY || 86);
const ocrLang = process.env.OCR_LANG || "tam+eng";
const ocrPsm = process.env.OCR_PSM || "6";
const concurrency = Math.max(1, Number(process.env.OCR_CONCURRENCY || Math.min(6, os.cpus().length)));

const dataDir = path.join(projectRoot, "data");
const ocrDir = path.join(dataDir, "ocr");
const pageDir = path.join(projectRoot, "public", "pages");

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd || projectRoot,
      env: { ...process.env, ...(options.env || {}) },
      stdio: options.stdio || ["ignore", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";

    if (child.stdout) {
      child.stdout.setEncoding("utf8");
      child.stdout.on("data", chunk => {
        stdout += chunk;
      });
    }

    if (child.stderr) {
      child.stderr.setEncoding("utf8");
      child.stderr.on("data", chunk => {
        stderr += chunk;
      });
    }

    child.on("error", reject);
    child.on("close", code => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(`${command} exited with ${code}\n${stderr}`));
      }
    });
  });
}

function pageFileName(pageNumber, extension) {
  return `page-${String(pageNumber).padStart(3, "0")}.${extension}`;
}

async function pageCountFromPdf() {
  const { stdout } = await run("pdfinfo", [pdfPath]);
  const match = stdout.match(/^Pages:\s+(\d+)/m);
  if (!match) {
    throw new Error("Could not determine PDF page count from pdfinfo output.");
  }
  return Number(match[1]);
}

async function renderedPageCount() {
  try {
    const files = await readdir(pageDir);
    return files.filter(file => /^page-\d{3}\.jpg$/i.test(file)).length;
  } catch {
    return 0;
  }
}

async function renderPages(pageCount) {
  await mkdir(pageDir, { recursive: true });
  const existing = await renderedPageCount();
  if (existing === pageCount) {
    console.log(`Page images already rendered (${existing}).`);
    return;
  }

  console.log(`Rendering ${pageCount} page images at ${renderDpi} DPI...`);
  await run("pdftoppm", [
    "-jpeg",
    "-r",
    String(renderDpi),
    "-jpegopt",
    `quality=${jpegQuality}`,
    pdfPath,
    path.join("public", "pages", "page")
  ], { stdio: ["ignore", "inherit", "inherit"] });
}

function normalizeWhitespace(text) {
  return text
    .replace(/\r/g, "")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function normalizeForSearch(text) {
  return text
    .normalize("NFC")
    .toLocaleLowerCase("ta-IN")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(text) {
  return normalizeForSearch(text)
    .split(" ")
    .filter(token => token.length > 1 && !/^\d+$/.test(token));
}

function tamilRatio(text) {
  const letters = [...text].filter(char => /\p{L}/u.test(char));
  if (!letters.length) return 0;
  const tamil = letters.filter(char => /[\u0B80-\u0BFF]/u.test(char));
  return tamil.length / letters.length;
}

function stripDecorativeNoise(line) {
  return line
    .replace(/[#$*_~=+|<>[\]{}\\/@]+/g, " ")
    .replace(/^[\d\s.,:;'"!?-]+|[\d\s.,:;'"!?-]+$/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function isGenericHeader(line, pageNumber) {
  const compact = line.replace(/[^\u0B80-\u0BFFA-Za-z]+/gu, "");

  return [
    /^ஸ்ரீ\s*[:!।]*$/u,
    /ராமா\s*நுஜாய\s+நம/u,
    /ராமாநுஜாய\s+நம/u,
    /நம[:：]?$/u,
    /^Page\s+\d+$/iu
  ].some(pattern => pattern.test(line)) || (pageNumber > 1 && /அஷ்டாத.*ரஹஸ/u.test(compact));
}

function noiseRatio(line) {
  const chars = [...line].filter(char => !/\s/u.test(char));
  if (!chars.length) return 1;
  const noisy = chars.filter(char => !/[\p{L}\p{N}\u0B80-\u0BFF]/u.test(char));
  return noisy.length / chars.length;
}

function titleScore(line) {
  let score = 0;
  const compact = line.replace(/\s+/g, "");
  const compactTamil = line.replace(/[^\u0B80-\u0BFF]/gu, "");
  const concise = compactTamil.length <= 34;

  if (/பதிப்புரை|முன்னுரை|முகவுரை|அணிந்துரை/u.test(line)) score += 12;
  if (concise && /ரஹஸ்ய|ரஹஸ|த்ரயம்|மாலை|பஞ்சகம்|ப்ரமாண|திரட்டு|பூஷணம்/u.test(line)) score += 7;
  if (concise && /முமுக்ஷுப்படி|பரந்தபடி|ச்ரிய.*படி/u.test(compactTamil)) score += 7;
  if (line.length >= 10 && line.length <= 45) score += 3;
  if (/[A-Za-z]/.test(line)) score -= 5;
  if (compact.length > 60) score -= 4;

  return score;
}

function inferTitle(text, pageNumber) {
  const candidates = text
    .split("\n")
    .slice(0, 18)
    .map(stripDecorativeNoise)
    .filter(line => line.length >= 6 && line.length <= 90)
    .filter(line => tamilRatio(line) > 0.25)
    .filter(line => noiseRatio(line) < 0.35)
    .filter(line => !/[A-Za-z]/.test(line) || tamilRatio(line) > 0.72)
    .filter(line => !isGenericHeader(line, pageNumber))
    .filter(line => !/^[\d\s.,:;()'"-]+$/.test(line));

  const [best] = candidates
    .map(line => ({ line, score: titleScore(line) }))
    .sort((a, b) => b.score - a.score);

  return best && best.score > 5 ? best.line : `Page ${pageNumber}`;
}

async function ocrPage(pageNumber) {
  const imageRel = path.join("public", "pages", pageFileName(pageNumber, "jpg"));
  const textPath = path.join(ocrDir, pageFileName(pageNumber, "txt"));

  if (!process.env.FORCE_OCR) {
    try {
      const existing = await readFile(textPath, "utf8");
      return normalizeWhitespace(existing);
    } catch {
      // Continue and create OCR text.
    }
  }

  const { stdout } = await run("tesseract", [
    imageRel,
    "stdout",
    "-l",
    ocrLang,
    "--psm",
    ocrPsm,
    "--oem",
    "1",
    "-c",
    "preserve_interword_spaces=1"
  ]);

  const text = normalizeWhitespace(stdout);
  await writeFile(textPath, `${text}\n`, "utf8");
  return text;
}

async function mapLimit(items, limit, worker) {
  const results = new Array(items.length);
  let nextIndex = 0;
  let completed = 0;

  async function loop() {
    while (nextIndex < items.length) {
      const index = nextIndex;
      nextIndex += 1;
      results[index] = await worker(items[index], index);
      completed += 1;
      if (completed % 10 === 0 || completed === items.length) {
        process.stdout.write(`\rOCR progress: ${completed}/${items.length}`);
      }
    }
  }

  await Promise.all(Array.from({ length: limit }, loop));
  process.stdout.write("\n");
  return results;
}

function buildSearchIndex(pages) {
  const index = {};

  for (const page of pages) {
    const uniqueTokens = new Set(tokenize(`${page.title}\n${page.text}`));
    for (const token of uniqueTokens) {
      if (!index[token]) {
        index[token] = [];
      }
      index[token].push(page.number);
    }
  }

  return Object.fromEntries(Object.entries(index).sort(([a], [b]) => a.localeCompare(b, "ta-IN")));
}

async function main() {
  await mkdir(dataDir, { recursive: true });
  await mkdir(ocrDir, { recursive: true });

  const pageCount = await pageCountFromPdf();
  await renderPages(pageCount);

  const pageNumbers = Array.from({ length: pageCount }, (_, index) => index + 1);
  console.log(`Running OCR with ${ocrLang}, psm ${ocrPsm}, concurrency ${concurrency}...`);
  const texts = await mapLimit(pageNumbers, concurrency, ocrPage);

  const pages = pageNumbers.map((pageNumber, index) => {
    const text = texts[index] || "";
    const normalized = normalizeForSearch(text);

    return {
      number: pageNumber,
      image: `public/pages/${pageFileName(pageNumber, "jpg")}`,
      title: inferTitle(text, pageNumber),
      text,
      characterCount: text.length,
      wordCount: normalized ? normalized.split(" ").length : 0
    };
  });

  const searchIndex = buildSearchIndex(pages);
  const generatedAt = new Date().toISOString();

  await writeFile(path.join(dataDir, "book.json"), JSON.stringify({
    metadata: {
      title: "அஷ்டாதச ரஹஸ்யம்",
      subtitle: "Astathasa Rahasyam",
      language: "Tamil",
      sourceFile: path.basename(pdfPath),
      pageCount,
      generatedAt,
      renderDpi,
      jpegQuality,
      ocr: {
        engine: "Tesseract",
        language: ocrLang,
        pageSegmentationMode: ocrPsm
      }
    },
    pages
  }, null, 2), "utf8");

  await writeFile(path.join(dataDir, "search-index.json"), JSON.stringify({
    generatedAt,
    tokenCount: Object.keys(searchIndex).length,
    index: searchIndex
  }), "utf8");

  console.log(`Wrote data/book.json and data/search-index.json with ${pages.length} pages.`);
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
