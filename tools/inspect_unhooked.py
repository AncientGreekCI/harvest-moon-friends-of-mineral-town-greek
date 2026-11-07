# -*- coding: utf-8 -*-
import json

data = json.load(open('tools/unhooked_strings.json', 'r', encoding='utf-8'))
print(f"Total unhooked unique strings: {len(data)}")

print("\n--- Sample 1: 0..40 ---")
for i, d in enumerate(data[:40]):
    print(f"{i:2d}: {d['addrs'][0]} ({len(d['addrs'])} addrs): {d['text']!r}")

print("\n--- Sample 2: 100..140 ---")
for i, d in enumerate(data[100:140], start=100):
    print(f"{i:2d}: {d['addrs'][0]} ({len(d['addrs'])} addrs): {d['text']!r}")

print("\n--- Sample 3: 500..540 ---")
for i, d in enumerate(data[500:540], start=500):
    print(f"{i:2d}: {d['addrs'][0]} ({len(d['addrs'])} addrs): {d['text']!r}")
