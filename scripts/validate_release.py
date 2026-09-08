"""Validate the distributable without network or third-party Python packages."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def validate(root=ROOT):
    errors = []
    marketplace = json.loads((root / '.agents/plugins/marketplace.json').read_text(encoding='utf-8'))
    for entry in marketplace['plugins']:
        plugin = root / entry['source']['path']
        manifest = json.loads((plugin / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
        if plugin.name != manifest['name'] or entry['name'] != manifest['name']:
            errors.append('Plugin name mismatch')
        for skill in (plugin / 'skills').glob('*/SKILL.md'):
            text = skill.read_text(encoding='utf-8')
            if not text.startswith('---\n') or '\nname:' not in text or '\ndescription:' not in text:
                errors.append(f'Invalid skill header: {skill.name}')
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if '://' not in link and not (skill.parent / link).is_file():
                    errors.append(f'Missing reference: {link}')
    for path in root.rglob('*'):
        if not path.is_file() or any(part in {'.git', '__pycache__', 'work'} for part in path.relative_to(root).parts):
            continue
        if path.name.startswith('.env') or path.suffix in {'.pem', '.key'}:
            errors.append(f'Unexpected credential file: {path.name}')
        if path.suffix in {'.md', '.json', '.yaml'}:
            text = path.read_text(encoding='utf-8')
            if re.search(r'[A-Za-z]:[\\/](?:Users|home)[\\/]', text):
                errors.append(f'Absolute personal path: {path.relative_to(root)}')
    if errors:
        raise ValueError('\n'.join(errors))
    return 'PASS: manifests, bundled references and portable paths'

if __name__ == '__main__':
    print(validate())
