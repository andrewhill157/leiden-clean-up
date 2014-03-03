"""
Andrew Hill
MacArthur Lab - 2014

Driver script for extracting and validating data from the leiden open variation databases.
"""

from macarthur_core.cluster import lsf
from macarthur_core.remapping import remapping
from macarthur_core.io import file_io
import subprocess
import argparse
import glob
import os

# Command line interface definition
parser = argparse.ArgumentParser(description='Driver script for extracting an validating data from the Leiden Open '
                                             'Variation Databases.')

group = parser.add_argument('-u', '--url', help='Input VCF file to be annotated.')
group = parser.add_argument('--no_download', default=False, action='store_true', help='Set to use extracted data files '
                                                                                     'rather than downloading new data.')
group = parser.add_argument('-o', '--output_directory', default='.', help='Output directory for files. Search directory '
                                                                          'for extracted data files if --use_files is '
                                                                          'specified.')

args = parser.parse_args()

output_directory = args.output_directory

if not args.no_download:
    # Download table data all genes at URL
    pipe = subprocess.Popen(['python', 'extract_data.py', '-a',
                             '-u', args.url,
                             '-o', output_directory], stdout=subprocess.PIPE)

    extract_data_log = pipe.communicate()[0]

    # Write log of execution to log file
    with open('extract_data.log', 'w') as f:
        f.write(extract_data_log)

# Produce VCF files
extracted_data_files = glob.glob(os.path.join(output_directory, '*.txt'))

remapping_errors = []
for data_file in extracted_data_files:
    output_file = os.path.splitext(data_file)[0] + '.vcf'
    errors = remapping.generate_vcf_from_hgvs(data_file, output_file, 'dna', 'protein')
    remapping_errors = remapping_errors + errors

file_io.write_table_to_file('remapping_errors.log', remapping_errors)

# Annotate VCF files
vcf_files = glob.glob(os.path.join(output_directory, '*.vcf'))

for vcf in vcf_files:
    # Submit LSF jobs for annotation
    base_file_name = os.path.basename(vcf)
    job_name = os.path.splitext(base_file_name)[0]

    annotated_file_name = job_name + '_ANNOTATED.vcf'
    lsf_output_file = job_name + '.o'
    command = 'python annotate_vcfs.py -i ' + vcf + ' -o ' + annotated_file_name

    lsf.bsub(command, job_name, lsf_output_file)

# Can we link validation/finalized file writing to this?
