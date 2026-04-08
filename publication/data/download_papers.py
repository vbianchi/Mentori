#!/usr/bin/env python3
"""
Download V4 Core Paper PDFs from Europe PMC and other open access sources.

Usage:
    uv run python datasets/download_papers.py
    uv run python datasets/download_papers.py --start 1 --end 10
    uv run python datasets/download_papers.py --dry-run
"""

import argparse
import asyncio
import httpx
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Output directory
DOWNLOAD_DIR = Path(__file__).parent / "downloaded_papers"

# Europe PMC direct PDF endpoint (most reliable for PMC papers)
EUROPEPMC_PDF = "https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf"

# Paper definitions: (id, filename, primary_url, fallback_url)
# Using Europe PMC URLs for PMC papers which work better for programmatic access
PAPERS = [
    # Bioinformatics/NGS Tools (1-10)
    (1, "nfcore_framework.pdf",
     # Nature Biotech - requires subscription, try PMC
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC7111497&blobtype=pdf",
     None),
    (2, "snakemake.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC8114187&blobtype=pdf",
     None),
    (3, "sarek_pipeline.pdf",
     # NAR Genomics - try Oxford Academic direct
     "https://watermark.silverchair.com/lqae031.pdf?token=AQECAHi208BE49Ooan9kkhW_Ercy7Dm3ZL_9Cf3qfKAc485ysgAAA",
     "https://academic.oup.com/nargab/article-pdf/6/2/lqae031/57658070/lqae031.pdf"),
    (4, "fastp.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC6129281&blobtype=pdf",
     None),
    (5, "multiqc.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC5039924&blobtype=pdf",
     None),
    (6, "star_aligner.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC3530905&blobtype=pdf",
     None),
    (7, "salmon.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC5600148&blobtype=pdf",
     None),
    (8, "deseq2.pdf",
     "https://link.springer.com/content/pdf/10.1186/s13059-014-0550-8.pdf",
     None),
    (9, "seqkit.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC5051824&blobtype=pdf",
     None),
    (10, "cutadapt.pdf",
     # EMBnet journal - direct download
     "https://journal.embnet.org/index.php/embnetjournal/article/download/200/479/1816",
     None),

    # Veterinary Epidemiology (11-20)
    (11, "asf_burkina_faso.pdf",
     "https://link.springer.com/content/pdf/10.1186/s12917-022-03166-y.pdf",
     None),
    (12, "hpai_netherlands.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11696498&blobtype=pdf",
     None),
    (13, "lsd_nepal.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC10974591&blobtype=pdf",
     None),
    (14, "bovine_tb_cameroon.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC10884586&blobtype=pdf",
     None),
    (15, "rabies_tanzania.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11482771&blobtype=pdf",
     None),
    (16, "ppr_ethiopia.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11457360&blobtype=pdf",
     None),
    (17, "brucellosis_ethiopia.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11002772&blobtype=pdf",
     None),
    (18, "fmd_review.pdf",
     "https://link.springer.com/content/pdf/10.1186/s13567-024-01404-z.pdf",
     None),
    (19, "hpai_canada.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11013356&blobtype=pdf",
     None),
    (20, "lsd_india.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11357335&blobtype=pdf",
     None),

    # Microbiome (21-30)
    (21, "livestock_gut_microbiome_review.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9736591&blobtype=pdf",
     None),
    (22, "pig_mags.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9431278&blobtype=pdf",
     None),
    (23, "swine_cultivation.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC8407297&blobtype=pdf",
     None),
    (24, "chicken_microbiome.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC10989779&blobtype=pdf",
     None),
    (25, "dairy_cow_feed.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11522680&blobtype=pdf",
     None),
    (26, "gut_meat_quality.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9445620&blobtype=pdf",
     None),
    (27, "inap_pipeline.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC10989900&blobtype=pdf",
     None),
    (28, "otu_vs_asv.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9029325&blobtype=pdf",
     None),
    (29, "16s_best_practices.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC8807179&blobtype=pdf",
     None),
    (30, "aquaculture_metagenomics.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9930364&blobtype=pdf",
     None),

    # AMR / One Health / Zoonotic (31-45)
    (31, "amr_one_health.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9047147&blobtype=pdf",
     None),
    (32, "amr_livestock_environment.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11016740&blobtype=pdf",
     None),
    (33, "amr_food_animals.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9133924&blobtype=pdf",
     None),
    (34, "one_health_framework.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9124177&blobtype=pdf",
     None),
    (35, "isse_framework_amr.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC8024545&blobtype=pdf",
     None),
    (36, "integrated_amr_surveillance.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11210117&blobtype=pdf",
     None),
    (37, "data_driven_one_health.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC8780196&blobtype=pdf",
     None),
    (38, "one_health_africa.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC10394936&blobtype=pdf",
     None),
    (39, "zoonotic_southeast_asia.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC10050087&blobtype=pdf",
     None),
    (40, "animal_agriculture_one_health.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11107239&blobtype=pdf",
     None),
    (41, "salmonella_wgs_amr.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC9804530&blobtype=pdf",
     None),
    (42, "campylobacter_wgs_thailand.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC10869288&blobtype=pdf",
     None),
    (43, "esbl_ecoli_food.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC11054374&blobtype=pdf",
     None),
    (44, "eu_amr_report_2022.pdf",
     "https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC10900121&blobtype=pdf",
     None),
    (45, "kenya_amr_digital.pdf",
     "https://www.frontiersin.org/articles/10.3389/fpubh.2024.1411962/pdf",
     None),
]


async def download_pdf(
    client: httpx.AsyncClient,
    paper_id: int,
    filename: str,
    url: str,
    fallback_url: Optional[str] = None,
) -> bool:
    """Download a single PDF file."""
    output_path = DOWNLOAD_DIR / filename

    if output_path.exists():
        logger.info(f"[{paper_id:02d}] SKIP: {filename} (already exists)")
        return True

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    urls_to_try = [url]
    if fallback_url:
        urls_to_try.append(fallback_url)

    for try_url in urls_to_try:
        try:
            logger.info(f"[{paper_id:02d}] Downloading {filename}...")
            response = await client.get(try_url, headers=headers, follow_redirects=True)

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")

                # Check if we got a PDF
                if "pdf" in content_type.lower() or response.content[:4] == b"%PDF":
                    output_path.write_bytes(response.content)
                    size_kb = len(response.content) / 1024
                    logger.info(f"[{paper_id:02d}] OK: {filename} ({size_kb:.0f} KB)")
                    return True
                else:
                    logger.warning(f"[{paper_id:02d}] Not a PDF: {content_type}")
            else:
                logger.warning(f"[{paper_id:02d}] HTTP {response.status_code}: {try_url[:60]}...")

        except Exception as e:
            logger.error(f"[{paper_id:02d}] Error: {e}")

    logger.error(f"[{paper_id:02d}] FAILED: {filename}")
    return False


async def download_all(start: int = 1, end: int = 45, dry_run: bool = False):
    """Download all papers in range."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    papers_to_download = [p for p in PAPERS if start <= p[0] <= end]

    if dry_run:
        logger.info("DRY RUN - would download:")
        for paper_id, filename, url, _ in papers_to_download:
            logger.info(f"  [{paper_id:02d}] {filename}")
        return

    logger.info(f"Downloading {len(papers_to_download)} papers to {DOWNLOAD_DIR}")
    logger.info("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        results = []
        for paper_id, filename, url, fallback in papers_to_download:
            success = await download_pdf(client, paper_id, filename, url, fallback)
            results.append((paper_id, filename, success))
            # Rate limiting
            await asyncio.sleep(1.0)

    # Summary
    logger.info("=" * 60)
    success_count = sum(1 for _, _, s in results if s)
    logger.info(f"Downloaded: {success_count}/{len(results)}")

    failed = [(pid, fn) for pid, fn, s in results if not s]
    if failed:
        logger.info("\nFailed downloads (manual download needed):")
        for pid, fn in failed:
            logger.info(f"  [{pid:02d}] {fn}")


def main():
    parser = argparse.ArgumentParser(description="Download V4 core papers")
    parser.add_argument("--start", type=int, default=1, help="Start paper ID")
    parser.add_argument("--end", type=int, default=45, help="End paper ID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    args = parser.parse_args()

    asyncio.run(download_all(args.start, args.end, args.dry_run))


if __name__ == "__main__":
    main()
