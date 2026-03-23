import json
import os
from os.path import getmtime
from zipfile import ZipFile

REPO = os.environ.get("GITHUB_REPOSITORY", "twelvehouse/DalamudPlugins")
BRANCH = os.environ.get("GITHUB_REF", "refs/heads/main").split("refs/heads/")[-1] or "main"
DOWNLOAD_URL = "https://github.com/{repo}/raw/{branch}/plugins/{name}/latest.zip"

MANIFEST_KEYS = [
    "Author",
    "Name",
    "Punchline",
    "Description",
    "Tags",
    "InternalName",
    "RepoUrl",
    "Changelog",
    "AssemblyVersion",
    "ApplicableVersion",
    "DalamudApiLevel",
    "IconUrl",
    "ImageUrls",
]


def main():
    plugins = collect_plugins()
    master = build_master(plugins)
    write_master(master)


def collect_plugins():
    """Collect (name, zip_path, manifest) tuples for all plugins with a latest.zip."""
    result = []
    plugins_root = os.path.join(".", "plugins")
    if not os.path.isdir(plugins_root):
        return result

    for name in sorted(os.listdir(plugins_root)):
        zip_path = os.path.join(plugins_root, name, "latest.zip")
        if not os.path.exists(zip_path):
            continue
        with ZipFile(zip_path) as z:
            manifest = json.loads(z.read(f"{name}.json").decode("utf-8"))
        result.append((name, zip_path, manifest))

    return result


def build_master(plugins):
    master = []
    for name, zip_path, manifest in plugins:
        entry = {k: manifest[k] for k in MANIFEST_KEYS if k in manifest}
        url = DOWNLOAD_URL.format(repo=REPO, branch=BRANCH, name=name)
        entry["DownloadLinkInstall"] = url
        entry["DownloadLinkUpdate"] = url
        entry["DownloadCount"] = 0
        entry["LastUpdate"] = str(int(getmtime(zip_path)))
        master.append(entry)
    return master


def write_master(master):
    with open("pluginmaster.json", "w", encoding="utf-8") as f:
        json.dump(master, f, indent=4, ensure_ascii=False)
    print(f"Written {len(master)} plugin(s) to pluginmaster.json")


if __name__ == "__main__":
    main()
