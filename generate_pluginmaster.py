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
    write_readme(master)


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
        metadata_path = os.path.join(plugins_root, name, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, encoding="utf-8") as f:
                manifest.update(json.load(f))
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


def write_readme(master):
    repo_url = f"https://raw.githubusercontent.com/{REPO}/main/pluginmaster.json"

    sections = []
    for plugin in master:
        name = plugin.get("Name", "")
        version = plugin.get("AssemblyVersion", "")
        punchline = plugin.get("Punchline", "")
        description = plugin.get("Description", "")
        icon_url = plugin.get("IconUrl", "")
        image_urls = plugin.get("ImageUrls", [])

        # Heading: icon (if available) + name + version
        if icon_url:
            heading = f'### <img src="{icon_url}" width="32" alt=""> &nbsp; {name} &nbsp; `v{version}`'
        else:
            heading = f"### {name} &nbsp; `v{version}`"

        # Description lines
        lines = [heading, ""]
        if punchline:
            lines.append(punchline)
        if description and description != punchline:
            lines.append(description)
        lines.append("")

        # Preview images (if available)
        if image_urls:
            img_tags = "\n  &nbsp;\n  ".join(
                f'<img src="{url}" width="380" alt="{name} preview">'
                for url in image_urls
            )
            lines.append(f"<p>\n  {img_tags}\n</p>")
            lines.append("")

        sections.append("\n".join(lines))

    plugins_section = "---\n\n" + "\n---\n\n".join(sections) + "\n---" if sections else "*(no plugins yet)*"

    readme = f"""\
# Dalamud Plugin Repository

Custom Dalamud plugin repository by [twelvehouse](https://github.com/twelvehouse).

## Setup

Add the following URL to **Dalamud → Settings → Experimental → Custom Plugin Repositories**:

```
{repo_url}
```

## Plugins

{plugins_section}
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("Updated README.md")


if __name__ == "__main__":
    main()
