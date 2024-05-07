import logging

# Setup the logger
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("[%(asctime)s %(levelname)s %(name)s] %(message)s")
)
# logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)

base_image = "localhost:30000/variant-discovery:20240416"
pb_image = "ghcr.io/unionai/dgx-parabricks:20240416"
seq_dir_pth = "s3://my-s3-bucket/my-data/sequences"
ref_loc = "s3://my-s3-bucket/my-data/refs/GRCh38_short.fasta"
ref_hash = str(hash(ref_loc))[:4]

# Tool config
fastp_cpu = "3"

test_assets = {
    "seq_dir": "/root/src/tests/assets/sequences/raw",
    "filt_dir": "/root/src/tests/assets/sequences/filtered",
    "bt2_sam_dir": "/root/src/tests/assets/alignments/bt2",
    "hs2_sam_dir": "/root/src/tests/assets/alignments/hs2",
    "pb_fq2bam_dir": "/root/src/tests/assets/alignments/pb_fq2bam",
    "pb_haplocall_dir": "/root/src/tests/assets/alignments/pb_haplocall",
    "sort_dir": "/root/src/tests/assets/alignments/sorted",
    "dedup_dir": "/root/src/tests/assets/alignments/deduped",
    "ref_path": "/root/src/tests/assets/references/GRCh38_short.fasta",
    "ref_dir": "/root/src/tests/assets/references/",
    "ref_fn": "GRCh38_short.fasta",
    "sites_path": "/root/src/tests/assets/sites/known_indels_trunc.hg38.vcf.gz",
    "sites_idx_path": "/root/src/tests/assets/sites/known_indels_trunc.hg38.vcf.gz.tbi",
    "vcf_path": "/root/src/tests/assets/vcfs/test_sample_test_caller.vcf",
    "vcf_idx_path": "/root/src/tests/assets/vcfs/test_sample_test_caller.vcf.gz.tbi",
    "vcf_dir": "/root/src/tests/assets/vcfs/",
    "idx_dir": "/root/src/tests/assets/indices",
    "bt2_idx_dir": "/root/src/tests/assets/indices/bt2",
    "hs2_idx_dir": "/root/src/tests/assets/indices/hs2",
    "bwa_idx_dir": "/root/src/tests/assets/indices/bwa",
    "fastqc_dir": "/root/src/tests/assets/fastqc",
}
