import gzip
import shutil
from pathlib import Path
from flytekit import kwtypes, task, Resources, current_context, TaskMetadata
from flytekit.extras.tasks.shell import OutputLocation, ShellTask
from flytekit.types.file import FlyteFile
from flytekit.types.directory import FlyteDirectory

from .config import ref_hash, base_image
from .sample_types import FiltSample, SamFile
from .utils import subproc_raise

hisat2_index = ShellTask(
    name="hisat2-index",
    debug=True,
    metadata=TaskMetadata(retries=3, cache=True, cache_version=ref_hash),
    requests=Resources(cpu="4", mem="10Gi"),
    container_image=base_image,
    script="""
    mkdir {outputs.idx}
    hisat2-build {inputs.ref} {outputs.idx}/hs2_idx
    """,
    inputs=kwtypes(ref=FlyteFile),
    output_locs=[
        OutputLocation(var="idx", var_type=FlyteDirectory, location="/root/idx")
    ],
)


@task(container_image=base_image, requests=Resources(cpu="4", mem="10Gi"))
def hisat2_align_paired_reads(idx: FlyteDirectory, fs: FiltSample) -> SamFile:
    idx.download()
    ldir = Path(current_context().working_directory)
    sam = ldir.joinpath(f"{fs.sample}_hisat2.sam")
    rep = ldir.joinpath(f"{fs.sample}_hisat2_report.txt")
    unc_r1 = ldir.joinpath(f"{fs.sample}_1.fq")
    unc_r2 = ldir.joinpath(f"{fs.sample}_2.fq")

    with gzip.open(fs.filt_r1, "rb") as gz_file, open(unc_r1, "wb") as out_file:
        shutil.copyfileobj(gz_file, out_file)

    with gzip.open(fs.filt_r2, "rb") as gz_file, open(unc_r2, "wb") as out_file:
        shutil.copyfileobj(gz_file, out_file)

    cmd = [
        "hisat2",
        "-x",
        f"{idx.path}/hs2_idx",
        "-1",
        unc_r1,
        "-2",
        unc_r2,
        "-S",
        sam,
        "--summary-file",
        rep,
    ]

    stdout, stderr = subproc_raise(cmd)

    return SamFile(
        sample=fs.sample, sam=FlyteFile(path=str(sam)), report=FlyteFile(path=str(rep))
    )
