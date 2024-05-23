# Ok, we are ready to begin and import all tools we will use in this colab:
import os
import numpy as np
import matplotlib.pyplot as plt
import py3Dmol
import biotite.structure.io as bsio
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from flytekit import ImageSpec, Resources, task, workflow
from unionbio.datatypes.reads import Reads
from unionbio.datatypes.protein import Protein
from unionbio.config import folding_img

@task(container_image=folding_img)
def prodigal_predict(in_seq: Reads) -> Protein:
    """
    Predicts protein sequences from a DNA sequence using Prodigal.
    """
    seq = in_seq.read1
    seq.download()

    prot = Protein(name=in_seq.sample)
    prot_out = prot.get_prot_fname()
    genes_out = prot.get_genes_fname()

    cmd = [
        "prodigal",
        "-i", seq.path,
        "-a", prot_out,
        "-o", genes_out,
    ]

    setattr(prot, "protein", prot_out)
    setattr(prot, "genes", genes_out)

    return prot