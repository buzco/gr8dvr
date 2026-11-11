"""Tiny 8051 assembler for our hooks: items are bytes, ('label', name), or ops needing label fixups."""
def assemble(org, items):
    labels, pc = {}, org
    sizes = []
    for it in items:
        if isinstance(it, tuple) and it[0] == 'label':
            labels[it[1]] = pc; sizes.append(0); continue
        if isinstance(it, tuple):
            n = {'sjmp':2,'jz':2,'jnz':2,'jc':2,'jnc':2,'jb':3,'jnb':3,'cjne':3,'ljmp':3,'lcall':3}[it[0]]
        else:
            n = len(it)
        sizes.append(n); pc += n
    out, pc = bytearray(), org
    for it, n in zip(items, sizes):
        if isinstance(it, tuple):
            op = it[0]
            if op == 'label': continue
            if op in ('ljmp', 'lcall'):
                t = labels[it[1]] if isinstance(it[1], str) else it[1]
                out += bytes([0x02 if op == 'ljmp' else 0x12, t >> 8, t & 0xFF])
            else:
                t = labels[it[-1]]
                rel = t - (pc + n); assert -128 <= rel <= 127, (it, rel)
                if op == 'sjmp': out += bytes([0x80, rel & 0xFF])
                elif op == 'jz': out += bytes([0x60, rel & 0xFF])
                elif op == 'jnz': out += bytes([0x70, rel & 0xFF])
                elif op == 'jc': out += bytes([0x40, rel & 0xFF])
                elif op == 'jnc': out += bytes([0x50, rel & 0xFF])
                elif op == 'cjne': out += bytes([0xB4, it[1], rel & 0xFF])
                elif op == 'jb': out += bytes([0x20, it[1], rel & 0xFF])
                elif op == 'jnb': out += bytes([0x30, it[1], rel & 0xFF])
        else:
            out += it
        pc += n
    return bytes(out), labels
