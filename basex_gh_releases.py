import os
import io
import tempfile
import subprocess
import checksum
import sys

from pathlib import Path
from string import Template
from typing import Optional, Dict

from github import Github


def get_chksum(url, installer):
    subprocess.call(["curl",
                     url,
                     "-o",
                     installer])
    chksum = checksum.get_for_file(installer, "sha512")
    os.remove(installer)
    return chksum


def find_and_replace_templates(package_name: str, directory: str, version: str,
                               tag: str, url: str, checksum: str,
                               fname: Optional[str], url64: Optional[str],
                               checksum64: Optional[str],
                               fname64: Optional[str],
                               notes: Optional[str]) -> None:
    os.mkdir(Path(directory) / "tools")
    os.mkdir(Path(directory) / "legal")
    values = dict(version=version,
                  tag=tag,
                  url=url,
                  checksum=checksum,
                  fname=fname,
                  url64=url64,
                  checksum64=checksum64,
                  fname64=fname64,
                  notes=notes)
    basepath = Path(os.getcwd()) / "template"
    templates = [
        package_name + ".nuspec", "tools/chocolateyinstall.ps1",
        "tools/chocolateyuninstall.ps1", "tools/LICENSE.txt"
    ]

    for template in templates:
        print(template)
        try:
            with io.open(basepath / template, "r", encoding="utf-8-sig") as f:
                contents = f.read()
                temp = Template(contents).safe_substitute(values)
                f = io.open(Path(directory) / template,
                            "a+",
                            encoding="utf-8",
                            errors="ignore")
                f.write(temp)
                f.close()
        except FileNotFoundError as err:
            print("Could not find file to be templated.")
            print(err)
    return


def main():
    pkgname = "BaseX"
    ext = "exe"
    gh = Github(os.environ['GH_TOKEN'])
    repo = gh.get_repo("BaseXdb/" + pkgname)
    tag = repo.get_tags()[0].name
    installer = "".join([pkgname, str("".join(tag.split("."))), ".", ext])
    print(installer)
    url = "/".join(["https://files.basex.org/releases", tag, installer])
    print(url)
    chksum = get_chksum(url, installer)
    tempdir = tempfile.mkdtemp()
    find_and_replace_templates(pkgname,
                               tempdir,
                               tag,
                               tag,
                               url,
                               chksum,
                               None,
                               None,
                               None,
                               None,
                               None)
    Path("build").mkdir(exist_ok=True)
    subprocess.call(["choco",
                     "pack",
                     Path(tempdir) / (pkgname + ".nuspec"),
                     "--outputdirectory",
                     "build"])


if __name__ == "__main__":
    main()
