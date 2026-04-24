#!/usr/bin/env python3
"""
concat_files.py — Concatène tous les fichiers ADR, BCM, templates et externals-templates en un seul document.

Parcourt récursivement les dossiers `adr/`, `bcm/`, `templates/` et `externals-templates/` pour produire
un fichier unique contenant l'ensemble du contenu, avec des séparateurs
indiquant le chemin de chaque fichier source.

Usage:
    python tools/concat_files.py                    # Affiche sur stdout
    python tools/concat_files.py -o output.txt      # Écrit dans un fichier
    python tools/concat_files.py --adr-only         # ADR uniquement
    python tools/concat_files.py --bcm-only         # BCM uniquement
    python tools/concat_files.py --templates-only   # Templates internes + externes
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, TextIO


# Extensions de fichiers à inclure
VALID_EXTENSIONS = {".md", ".yaml", ".yml"}


def find_files(directory: Path, extensions: set[str] | None = None) -> List[Path]:
    """
    Trouve récursivement tous les fichiers avec les extensions spécifiées.
    
    Args:
        directory: Dossier racine à parcourir
        extensions: Extensions à inclure (ex: {".md", ".yaml"})
    
    Returns:
        Liste de chemins triés par ordre alphabétique
    """
    if extensions is None:
        extensions = VALID_EXTENSIONS
    
    if not directory.exists():
        return []
    
    files = []
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            # Exclure les fichiers __pycache__
            if "__pycache__" not in str(path):
                files.append(path)
    
    return sorted(files)


def format_separator(file_path: Path, repo_root: Path) -> str:
    """
    Génère un séparateur visuel pour un fichier.
    
    Args:
        file_path: Chemin absolu du fichier
        repo_root: Racine du repository pour afficher le chemin relatif
    
    Returns:
        Chaîne de séparation formatée
    """
    relative_path = file_path.relative_to(repo_root)
    width = 80
    separator_line = "=" * width
    
    return f"""
{separator_line}
FILE: {relative_path}
{separator_line}
"""


def concat_files(
    files: List[Path],
    repo_root: Path,
    output: TextIO
) -> int:
    """
    Concatène les fichiers avec séparateurs et les écrit dans output.
    
    Args:
        files: Liste des fichiers à concaténer
        repo_root: Racine du repository
        output: Flux de sortie (fichier ou stdout)
    
    Returns:
        Nombre de fichiers traités
    """
    count = 0
    
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
            separator = format_separator(file_path, repo_root)
            output.write(separator)
            output.write(content)
            if not content.endswith("\n"):
                output.write("\n")
            count += 1
        except Exception as e:
            print(f"⚠️  Erreur lecture {file_path}: {e}", file=sys.stderr)
    
    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Concatène les fichiers ADR, BCM, templates et externals-templates en un seul document.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python tools/concat_files.py                    # Tout sur stdout
  python tools/concat_files.py -o context.txt     # Sauvegarde dans un fichier
  python tools/concat_files.py --adr-only         # ADR uniquement
  python tools/concat_files.py --bcm-only         # BCM uniquement
    python tools/concat_files.py --templates-only   # Templates + externals-templates uniquement
  python tools/concat_files.py --ext .yaml        # YAML uniquement
"""
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Fichier de sortie (défaut: stdout)"
    )
    
    parser.add_argument(
        "--adr-only",
        action="store_true",
        help="Concatène uniquement les fichiers ADR"
    )
    
    parser.add_argument(
        "--bcm-only",
        action="store_true",
        help="Concatène uniquement les fichiers BCM"
    )

    parser.add_argument(
        "--templates-only",
        action="store_true",
        help="Concatène uniquement les fichiers templates (templates/ + externals-templates/)"
    )
    
    parser.add_argument(
        "--ext",
        type=str,
        action="append",
        dest="extensions",
        help="Extensions à inclure (peut être répété, ex: --ext .yaml --ext .md)"
    )
    
    parser.add_argument(
        "--no-separator",
        action="store_true",
        help="Désactive les séparateurs entre fichiers"
    )
    
    args = parser.parse_args()
    
    # Détermination de la racine du repository
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    
    adr_dir = repo_root / "adr"
    bcm_dir = repo_root / "bcm"
    templates_dir = repo_root / "templates"
    externals_templates_dir = repo_root / "externals-templates"
    
    # Extensions à utiliser
    extensions = set(args.extensions) if args.extensions else VALID_EXTENSIONS
    
    # Collecte des fichiers selon les options
    all_files: List[Path] = []
    
    selected_only_modes = sum([args.adr_only, args.bcm_only, args.templates_only])
    if selected_only_modes > 1:
        parser.error("--adr-only, --bcm-only et --templates-only sont mutuellement exclusifs")
    
    if args.adr_only:
        adr_files = find_files(adr_dir, extensions)
        all_files.extend(adr_files)
    elif args.bcm_only:
        bcm_files = find_files(bcm_dir, extensions)
        all_files.extend(bcm_files)
    elif args.templates_only:
        templates_files = find_files(templates_dir, extensions)
        externals_templates_files = find_files(externals_templates_dir, extensions)
        all_files.extend(templates_files)
        all_files.extend(externals_templates_files)
    else:
        adr_files = find_files(adr_dir, extensions)
        bcm_files = find_files(bcm_dir, extensions)
        templates_files = find_files(templates_dir, extensions)
        externals_templates_files = find_files(externals_templates_dir, extensions)
        all_files.extend(adr_files)
        all_files.extend(bcm_files)
        all_files.extend(templates_files)
        all_files.extend(externals_templates_files)
    
    if not all_files:
        print("⚠️  Aucun fichier trouvé.", file=sys.stderr)
        return 1
    
    # Sortie
    if args.output:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as f:
            count = concat_files(all_files, repo_root, f)
        print(f"✅ {count} fichiers concaténés dans {output_path}", file=sys.stderr)
    else:
        count = concat_files(all_files, repo_root, sys.stdout)
        print(f"\n# Total: {count} fichiers concaténés", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
