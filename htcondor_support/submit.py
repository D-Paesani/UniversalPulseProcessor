import os
import sys
import argparse 
import pandas as pd
import glob
import uproot
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import subprocess

preprint = "----------------->   "

#################################################################################################################################################################

def merge(opts="", infile="", outfile="", force=0):
    if force: os.system("rm -f {outfile}")
    os.system(F"hadd {opts} {outfile} {infile}")

#################################################################################################################################################################

rundict = "runlist.csv"
df = pd.read_csv(rundict, sep=" ", header=None)
df.columns = ["run", "typ", "orientation", "label", "bias_series", "bias_parallel"]

print(preprint, "Retrieving run list from ", rundict)
print(df.head())

#################################################################################################################################################################

parser = argparse.ArgumentParser(description='Wave reco H2 2023')

parser.add_argument('runlist',        type=str)
parser.add_argument('--force',        type=bool,  default=0)
parser.add_argument('--tag',          type=str,   default="")
parser.add_argument('--minevperjobs', type=int,   default=3000)
parser.add_argument('--mergeout',     type=int,   default=1)

parser.add_argument('--dry',          type=str,   default="")
parser.add_argument('--opts',         type=str,   default="")
parser.add_argument('--nspecs',       type=int,   default=20)
parser.add_argument('--evtp',         type=int,   default=-1)

args = parser.parse_args()
if args.tag != "": args.tag = "_" + args.tag
argstofwd = ['opts', 'dry', 'nspecs', 'evtp']

#################################################################################################################################################################

for ii in df["run"].astype(int) if args.runlist == "all" else [int(item) for item in args.runlist.split(' ')]:
  
    print(preprint, "processing run", args.runlist)
    
    afspath =           "/afs/cern.ch/user/d/dpaesani/public/H2_23_ana"
    scriptpath =        F"{afspath}/reco.py"
    dumppath =          F"{afspath}/condor_out/run{ii}{args.tag}"
    fcondor =           F"{dumppath}/jobsub{ii}{args.tag}.condor"
    inpath =            F"/eos/project/i/insulab-como/testBeam/TB_H2_2023_08_HIKE/MATTIA_WRITE_HERE/splitted/run700{ii}_%06d.root"
    inpathglob =        inpath.replace("%06d", "*")
    outpath =           F"/eos/user/d/dpaesani/data/H2_23/reco/run{ii}{args.tag}"
    outmerged =         F"/eos/user/d/dpaesani/data/H2_23/reco/run{ii}{args.tag}.root"
    outfile =           outpath + F"/run{ii}{args.tag}"
    spill_list_path =   f"{dumppath}/spill_list_%d.txt"
    jobflav =           "espresso"
    
    print(preprint, "outdir: ", outpath)
    
    row = df[df["run"] == ii]
    
    if len(glob.glob(outpath)) > 0:
        print(preprint, "already processed")
        if not args.force: 
            print(preprint, "skipping")
            continue
        else: 
            print(preprint, "reprocessing")
            os.system(F"rm -rf {outpath}/*")

    os.system(F"mkdir -p {outpath}")
    os.system(F"rm -rf {dumppath}")
    os.system(F"mkdir -p {dumppath}")

    spill_n = 0
    temp_evcounter = 0
    temp_spill_list = []
    job_counter = 0
    spill_file_list = glob.glob(inpathglob)
    spill_file_count = len(spill_file_list)
    
    for file_n, spill_file in enumerate(spill_file_list):
        
        spill_n = int(spill_file.split("_")[-1].split(".root")[0])
        temp_spill_list.append(str(spill_n))

        try:
            temp_evcounter += uproot.open(spill_file)["t"].num_entries
        except:
            print(preprint, F"skipping damaged file {spill_file}")
        
        if file_n == spill_file_count-1 or temp_evcounter > args.minevperjobs:
            print(preprint, f"writing in {spill_list_path%job_counter}")
            open(spill_list_path%job_counter, "w").write(",".join(temp_spill_list))
            job_counter += 1
            temp_spill_list = []
            temp_evcounter = 0
        spill_n += 1  

    argstring = F"{row.typ[0]} {inpath} {outfile} {spill_list_path}"

    # for key in vars(args):      
    #     if key not in ['runlist', 'force', 'minevperjobs', 'afspath']:
    #         if vars(args)[key] != "": argstring += F" --{key} {vars(args)[key]} "
    
    for key in argstofwd:      
        if vars(args)[key] != "": argstring += F" --{key} {vars(args)[key]} "

    njobs = job_counter-1
    
    sub = open("jobsub.condor", "r").read()
    sub = sub.replace(F"$*",            argstring)
    sub = sub.replace(F"$condorfolder", dumppath)
    sub = sub.replace(F"$nrun",         f"{ii}")
    sub = sub.replace(F"$njobs",        str(njobs))
    sub = sub.replace(F"$ScriptPath",   scriptpath)
    sub = sub.replace(F"$jobflav",      jobflav)
    
    f = open(fcondor, "w")
    f.write(sub)
    f.close()

    os.system(F"condor_submit {fcondor}")
    os.system("condor_q")
    
    if args.mergeout:
        
        pool = ThreadPoolExecutor()
        f = pool.submit(subprocess.call, F"/usr/bin/condor_wait {dumppath}/log*", shell=True)
        callback = lambda x: merge(opts="",     infile=F"{outpath}/{outpath.split('/')[-1]}*.root",         outfile=outmerged, force=1)
        callback2 = lambda x: merge(opts="",    infile=F"{outpath}/{outpath.split('/')[-1]}*_specs.root",   outfile=outmerged.replace(".root", "_specs.root"), force=1)
        f.add_done_callback(callback)
        f.add_done_callback(callback2)
        pool.shutdown(wait=False) 


