from typing import List, Tuple
from pathlib import Path
from flytekit import task, Resources, current_context
from flytekit.extras.tasks.shell import subproc_execute
from flytekit.types.directory import FlyteDirectory
from flytekit.types.file import FlyteFile
# from flytekitplugins.dgx import DGXConfig

from config import pb_image
from datatypes.alignment import Alignment
from datatypes.reference import Reference
from datatypes.reads import Reads
from datatypes.known_sites import Sites
from datatypes.variants import VCF


# Supported DGX instances:
# dgxa100.80g.1.norm, dgxa100.80g.2.norm, dgxa100.80g.4.norm, dgxa100.80g.8.norm
# @task(task_config=DGXConfig(instance="dgxa100.80g.1.norm"), container_image=pb_image)
@task(requests=Resources(gpu="1", mem="32Gi", cpu="32"), container_image=pb_image)
def fq2bam(read_obj: Reads, sites: Sites, ref: Reference) -> Alignment:
    """
    Takes an input directory containing sequence data and an indexed reference genome and
    performs alignment using Parabricks' fq2bam tool.

    Args:
        

    Returns:
        
    """

    RGTAG = "@RG\tID:HG002\tLB:lib\tPL:Illumina\tSM:HG002\tPU:HG002"
    read_obj.read1.download()
    read_obj.read2.download()
    sites.sites.download()
    sites.idx.download()
    ref.ref_dir.download()

    al_out = Alignment(sample=read_obj.sample, aligner="pbrun_fq2bam")

    bam_out = al_out.get_alignment_fname()
    bam_idx_out = al_out.get_alignment_idx_fname()
    recal_out = al_out.get_bqsr_fname()

    out, err = subproc_execute(
        [
            "pbrun",
            "fq2bam",
            "--ref",
            str(ref.get_ref_path()),
            "--in-fq",
            str(read_obj.read1.path),
            str(read_obj.read2.path),
            RGTAG,
            "--knownSites",
            str(sites[0].path),
            "--out-bam",
            bam_out,
            "--out-recal-file",
            recal_out,
        ]
    )

    setattr(al_out, "alignment", FlyteFile(path=bam_out))
    setattr(al_out, "alignment_index", FlyteFile(path=bam_idx_out))
    setattr(al_out, "recal_file", FlyteFile(path=recal_out))

    return FlyteFile(path=bam_out), FlyteFile(path=recal_out)


@task(requests=Resources(gpu="1", mem="32Gi", cpu="32"), container_image=pb_image)
# @task(task_config=DGXConfig(instance="dgxa100.80g.1.norm"), container_image=pb_image)
def basic_align(indir: FlyteDirectory) -> Tuple[FlyteFile, str]:
    """
    Aligns paired-end sequencing reads using BWA-MEM and GATK tools, and returns the path to the processed BAM file
    and the elapsed time for the alignment process.

    Args:
        indir (FlyteDirectory): The input directory containing sequencing read files and reference data.

    Returns:
        FlyteFile: The path to the processed BAM file in FlyteFile format.
    """
    indir.download()
    loc_dir = Path(indir.path)
    r1 = loc_dir.joinpath("Data/sample_1.fq.gz")
    r2 = loc_dir.joinpath("Data/sample_2.fq.gz")
    ref = loc_dir.joinpath("Ref/Homo_sapiens_assembly38.fasta")
    sites = loc_dir.joinpath("Ref/Homo_sapiens_assembly38.known_indels.vcf.gz")
    bampath = "bwa_mem_out.bam"

    cmd = " ".join(
        [
            "bwa",
            "mem",
            "-t",
            "32",
            "-K",
            "10000000",
            "-R",
            r'"@RG\tID:sample_rg1\tLB:lib1\tPL:bar\tSM:sample\tPU:sample_rg1"',
            str(ref),
            str(r1),
            str(r2),
            "|",
            "java",
            "-jar",
            "/usr/local/bin/gatk",
            "SortSam",
            "--MAX_RECORDS_IN_RAM",
            "5000000",
            "-I",
            "/dev/stdin",
            "-O",
            bampath,
            "--SORT_ORDER",
            "coordinate",
        ]
    )

    out1, err1 = subproc_execute(cmd, shell=True)

    dup_bam = "mark_dups.bam"
    out2, err2 = subproc_execute(
        [
            "java",
            "-jar",
            "/usr/local/bin/gatk",
            "MarkDuplicates",
            "-I",
            bampath,
            "-O",
            dup_bam,
            "-M",
            "metrics.txt",
        ]
    )

    recal_out = "recal_data.table"
    out3, err3 = subproc_execute(
        [
            "java",
            "-jar",
            "/usr/local/bin/gatk",
            "BaseRecalibrator",
            "--input",
            dup_bam,
            "--output",
            recal_out,
            "--known-sites",
            str(sites),
            "--reference",
            str(ref),
        ]
    )

    return FlyteFile(path=dup_bam)

@task(requests=Resources(gpu="1", mem="32Gi", cpu="32"), container_image=pb_image)
def pb_deepvar(al: Alignment, ref: Reference) -> VCF:
    """
    Takes an input directory containing BAM files and an indexed reference genome and
    performs variant calling using Parabricks' deepvariant tool.

    Args:


    Returns:

    """
    ref.ref_dir.download()
    al.alignment.download()
    al.alignment_idx.download()

    vcf_out = VCF(sample=al.sample, caller="pbrun_deepvariant")
    vcf_fname = vcf_out.get_vcf_fname()
    vcf_idx_fname = vcf_out.get_vcf_idx_fname()

    out, err = subproc_execute(
        [
            "pbrun",
            "deepvariant",
            "--ref",
            str(ref.get_ref_path()),
            "--in-bam",
            str(al.alignment.path),
            "--out-variants",
            vcf_out
        ]
    )

    setattr(vcf_out, "vcf", FlyteFile(path=vcf_fname))
    setattr(vcf_out, "vcf_idx", FlyteFile(path=vcf_idx_fname))

    deepvar_dir = FlyteDirectory(path="/tmp")
    return deepvar_dir

@task(requests=Resources(gpu="1", mem="32Gi", cpu="32"), container_image=pb_image)
def pb_haplocall(al: Alignment, ref: Reference) -> VCF:
    """
    Takes an input directory containing BAM files and an indexed reference genome and
    performs variant calling using Parabricks' accelerated version of GATK's HaplotypeCaller.

    Args:

    Returns:

    """
    ref.ref_dir.download()
    al.alignment.download()
    al.alignment_idx.download()
    al.bqsr_report.download()

    vcf_out = VCF(sample=al.sample, caller="pbrun_deepvariant")
    vcf_fname = vcf_out.get_vcf_fname()
    vcf_idx_fname = vcf_out.get_vcf_idx_fname()

    out, err = subproc_execute(
        [
            "pbrun",
            "deepvariant",
            "--ref",
            str(ref.get_ref_path()),
            "--in-bam",
            str(al.alignment.path),
            "--in-recal-file",
            str(al.bqsr_report.path),
            "--out-variants",
            vcf_out
        ]
    )

    setattr(vcf_out, "vcf", FlyteFile(path=vcf_fname))
    setattr(vcf_out, "vcf_idx", FlyteFile(path=vcf_idx_fname))

    deepvar_dir = FlyteDirectory(path="/tmp")
    return deepvar_dir


