"""Helpers for RetroArch (mGBA core) save states -> ROM tracing.
  python state_tools.py STATE_FILE [min_tiles]      (ROM path from env HM_ROM)
Decodes the RZIP/RASTATE container and lists runs of 8x8 4bpp tiles in the state's memory that are byte-identical
to data in the ROM (tile-aligned in the state, any 2-byte alignment in the ROM). Uncompressed sprites/UI show up as
runs; BG map art did NOT match in the farm state (see HANDOVER.md).
Container facts: '#RZIPv\\x01#' + u32 chunk size + u64 total size, then [u32 length][zlib data] chunks.
Decoded: 'RASTATE\\x01' then chunk 'MEM ' (+u32 size); the mGBA state starts at byte 16 (versionMagic, bios crc,
ROM CRC32 at +8, title at +0x10, ARM registers from +0x20). Video memory offsets in this mGBA version are NOT confirmed."""
import os, struct, sys, zlib
def rzip(path):
    s = open(path, 'rb').read()
    assert s[:6] == b'#RZIPv', 'not an RZIP state'
    p = 20; out = b''
    while p < len(s):
        n = struct.unpack('<I', s[p:p+4])[0]; p += 4
        out += zlib.decompress(s[p:p+n]); p += n
    return out
def runs(state, rom, min_tiles=4):
    idx = {}
    for p in range(0, len(rom) - 31, 2):
        k = rom[p:p+32]
        if k not in idx: idx[k] = p
    res = []; cur = None
    for off in range(0, len(state) - 31, 32):
        k = state[off:off+32]; src = idx.get(k) if len(set(k)) > 3 else None
        if src is not None and cur and src == cur[1] + 32 * cur[2]:
            cur[2] += 1
        elif src is not None:
            if cur and cur[2] >= min_tiles: res.append(cur)
            cur = [off, src, 1]
        else:
            if cur and cur[2] >= min_tiles: res.append(cur)
            cur = None
    if cur and cur[2] >= min_tiles: res.append(cur)
    return res
if __name__ == '__main__':
    st = rzip(sys.argv[1]); rom = open(os.environ.get('HM_ROM', 'Harvest_Moon_-_Friends_of_Mineral_Town__USA_.gba'), 'rb').read()
    print('state bytes', len(st), 'ROM CRC32 in state:', hex(struct.unpack_from('<I', st, 16 + 8)[0]))
    for off, src, n in runs(st, rom, int(sys.argv[2]) if len(sys.argv) > 2 else 4):
        print('state 0x%05x -> ROM 0x%06x  x%d tiles' % (off, src, n))
