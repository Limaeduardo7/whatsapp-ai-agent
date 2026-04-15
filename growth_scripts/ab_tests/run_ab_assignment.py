#!/usr/bin/env python3
"""Atribuição determinística de variante A/B por lead_id.
Uso:
  python3 run_ab_assignment.py --lead 5511999999999
"""
import argparse
import hashlib

def assign_variant(lead_id: str) -> str:
    digest = hashlib.sha256(lead_id.encode('utf-8')).hexdigest()
    bucket = int(digest, 16) % 2
    return 'A' if bucket == 0 else 'B'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lead', required=True, help='Lead ID único')
    args = parser.parse_args()
    print(assign_variant(args.lead))
