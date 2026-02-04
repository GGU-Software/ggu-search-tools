#!/usr/bin/env python3
"""Update registry with indexed tracking."""
import yaml
from datetime import datetime
from pathlib import Path

def main():
    registry_path = Path(__file__).parent.parent / 'config' / 'norms-registry.yaml'

    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # Add indexed tracking to each norm
    indexed_date = datetime.now().strftime('%Y-%m-%d')
    indexed_count = 0

    for norm in data.get('norms', []):
        if norm.get('status') in ('found', 'withdrawn_only'):
            norm['indexed'] = True
            norm['indexed_date'] = indexed_date
            indexed_count += 1
        else:
            norm['indexed'] = False
            norm['indexed_date'] = None

    # Add index summary
    data['index_summary'] = {
        'last_indexed': indexed_date,
        'pinecone_assistant': 'ggu-techdoc-search',
        'total_indexed': indexed_count,
        'total_norms': len(data['norms'])
    }

    # Save
    with open(registry_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print('Registry updated with indexed tracking')
    print(f"  Total norms: {data['index_summary']['total_norms']}")
    print(f"  Indexed: {data['index_summary']['total_indexed']}")

if __name__ == '__main__':
    main()
