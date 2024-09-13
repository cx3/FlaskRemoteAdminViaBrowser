import os
from pathlib import Path
from typing import Optional, Tuple

import bz2
import zlib
import gzip
import lzma
import py7zr
import zipfile
import rarfile
import tarfile
# import arjfile
import cabarchive

"""
Powered by Microsoft Copilot. Not all functions tested yet.
"""


def list_archive_file(archive_file_path: str, archive_password: Optional[str] = None):
    def list_files_in_zip(file_path, password=None):
        with zipfile.ZipFile(file_path, 'r') as archive:
            if password:
                archive.setpassword(password.encode())
            return [{'name': f.filename, 'size': f.file_size} for f in archive.infolist()]

    def list_files_in_rar(file_path, password=None):
        with rarfile.RarFile(file_path, 'r') as archive:
            if password:
                archive.setpassword(password)
            return [{'name': f.filename, 'size': f.file_size} for f in archive.infolist()]

    def list_files_in_7z(file_path, password=None):
        with py7zr.SevenZipFile(file_path, 'r', password=password) as archive:
            return [{'name': f.filename, 'size': f.file_size} for f in archive.getnames()]

    def list_files_in_tar(file_path, password=None):
        with tarfile.open(file_path, 'r') as archive:
            return [{'name': f.name, 'size': f.size} for f in archive.getmembers()]

    def list_files_in_gz(file_path, password=None):
        with gzip.open(file_path, 'rb') as f:
            return [{'name': file_path, 'size': len(f.read())}]

    def list_files_in_bz2(file_path, password=None):
        with bz2.open(file_path, 'rb') as f:
            return [{'name': file_path, 'size': len(f.read())}]

    def list_files_in_xz(file_path, password=None):
        with lzma.open(file_path, 'rb') as f:
            return [{'name': file_path, 'size': len(f.read())}]

    def list_files_in_cab(file_path, password=None):
        with cabarchive.CabArchive(file_path, 'r') as archive:
            return [{'name': f.filename, 'size': f.file_size} for f in archive.infolist()]

    def list_files_in_z(file_path, password=None):
        with open(file_path, 'rb') as f:
            return [{'name': file_path, 'size': len(zlib.decompress(f.read()))}]

    def list_files_in_tgz(file_path, password=None):
        return list_files_in_tar(file_path, password)

    def list_files_in_tbz2(file_path, password=None):
        return list_files_in_tar(file_path, password)

    def list_files_in_lz(file_path, password=None):
        with lzma.open(file_path, 'rb') as f:
            return [{'name': file_path, 'size': len(f.read())}]

    def list_files_in_jar(file_path, password=None):
        return list_files_in_zip(file_path, password)

    def list_files_in_war(file_path, password=None):
        return list_files_in_zip(file_path, password)

    def list_files_in_apk(file_path, password=None):
        return list_files_in_zip(file_path, password)

    name = archive_file_path.replace('\\', '/').split('/')[-1]
    ext = name.split('.')[-1] if '.' in name else name[:-4]

    for func_name, func_obj in vars().items():
        if func_name.startswith('list_') and func_name.endswith(ext):
            return func_obj(archive_file_path, archive_password)
    raise TypeError('Cannot select function to list files in archive')

#############################################################


def extract_archive_file(archive_file_path: str, dest_dir: Path or str, archive_password: Optional[str]):

    def extract_files_in_zip(file_path, dest_dir, password=None):
        with zipfile.ZipFile(file_path, 'r') as archive:
            if password:
                archive.setpassword(password.encode())
            archive.extractall(path=dest_dir)

    def extract_files_in_rar(file_path, dest_dir, password=None):
        with rarfile.RarFile(file_path, 'r') as archive:
            if password:
                archive.setpassword(password)
            archive.extractall(path=dest_dir)

    def extract_files_in_7z(file_path, dest_dir, password=None):
        with py7zr.SevenZipFile(file_path, 'r', password=password) as archive:
            archive.extractall(path=dest_dir)

    def extract_files_in_tar(file_path, dest_dir, password=None):
        with tarfile.open(file_path, 'r') as archive:
            archive.extractall(path=dest_dir)

    def extract_files_in_gz(file_path, dest_dir, password=None):
        with (gzip.open(file_path, 'rb') as f_in):
            with open(
                    os.path.join(dest_dir, os.path.basename(file_path).replace('.gz', '')), 'wb') as f_out:
                f_out.write(f_in.read())

    def extract_files_in_bz2(file_path, dest_dir, password=None):
        with bz2.open(file_path, 'rb') as f_in:
            with open(os.path.join(dest_dir, os.path.basename(file_path).replace('.bz2', '')), 'wb') as f_out:
                f_out.write(f_in.read())

    def extract_files_in_xz(file_path, dest_dir, password=None):
        with lzma.open(file_path, 'rb') as f_in:
            with open(os.path.join(dest_dir, os.path.basename(file_path).replace('.xz', '')), 'wb') as f_out:
                f_out.write(f_in.read())

    '''def extract_files_in_arj(file_path, dest_dir, password=None):
        with arj.ARJFile(file_path, 'r') as archive:
            if password:
                archive.setpassword(password)
            archive.extractall(path=dest_dir)'''

    def extract_files_in_cab(file_path, dest_dir, password=None):
        with cabarchive.CabArchive(file_path, 'r') as archive:
            archive.extractall(path=dest_dir)

    def extract_files_in_z(file_path, dest_dir, password=None):
        with open(file_path, 'rb') as f_in:
            with open(os.path.join(dest_dir, os.path.basename(file_path).replace('.z', '')), 'wb') as f_out:
                f_out.write(zlib.decompress(f_in.read()))

    def extract_files_in_tgz(file_path, dest_dir, password=None):
        return extract_files_in_tar(file_path, dest_dir, password)

    def extract_files_in_tbz2(file_path, dest_dir, password=None):
        return extract_files_in_tar(file_path, dest_dir, password)

    def extract_files_in_lz(file_path, dest_dir, password=None):
        with lzma.open(file_path, 'rb') as f_in:
            with open(os.path.join(dest_dir, os.path.basename(file_path).replace('.lz', '')), 'wb') as f_out:
                f_out.write(f_in.read())

    def extract_files_in_jar(file_path, dest_dir, password=None):
        return extract_files_in_zip(file_path, dest_dir, password)

    def extract_files_in_war(file_path, dest_dir, password=None):
        return extract_files_in_zip(file_path, dest_dir, password)

    def extract_files_in_apk(file_path, dest_dir, password=None):
        return extract_files_in_zip(file_path, dest_dir, password)

    name = archive_file_path.replace('\\', '/').split('/')[-1]
    ext = name.split('.')[-1] if '.' in name else name[:-4]

    for func_name, func_obj in vars().items():
        if func_name.startswith('extract_') and func_name.endswith(ext):
            return func_obj(archive_file_path, dest_dir, archive_password)
    raise TypeError('Cannot select function to list files in archive')
