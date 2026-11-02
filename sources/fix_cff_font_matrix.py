"""Restore the CID-keyed CFF FontMatrix to match the font's units per em."""

import argparse
import math
import os
import stat
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont


def matches(matrix, expected):
    return len(matrix) == 6 and all(
        math.isclose(value, target, rel_tol=0, abs_tol=1e-8)
        for value, target in zip(matrix, expected)
    )


def fix_font(path):
    path = Path(path)
    font = TTFont(path, recalcTimestamp=False)
    if 'CFF ' not in font:
        raise ValueError('Expected a CFF OpenType font')
    cff = font['CFF '].cff
    if len(cff.topDictIndex) != 1:
        raise ValueError('Expected one CFF Top DICT')
    top = cff.topDictIndex[0]
    if not hasattr(top, 'ROS') or not hasattr(top, 'FDArray') or not top.FDArray:
        raise ValueError('Expected a CID-keyed CFF font with font dictionaries')

    scale = 1 / font['head'].unitsPerEm
    expected = [scale, 0, 0, scale, 0, 0]
    top_matrix = top.rawDict.get('FontMatrix')
    fd_matrices = [fd.rawDict.get('FontMatrix') for fd in top.FDArray]
    if top_matrix is not None:
        if matches(top_matrix, expected) and all(matrix is None for matrix in fd_matrices):
            print('CFF FontMatrix already matches units per em:', path)
            return
        raise ValueError('Unexpected Top DICT FontMatrix; review before modifying')
    if any(matrix is not None and not matches(matrix, expected) for matrix in fd_matrices):
        raise ValueError('Unexpected Font DICT FontMatrix; review before modifying')
    missing = [fd for fd, matrix in zip(top.FDArray, fd_matrices) if matrix is None]
    if not missing:
        print('CFF FontMatrix already matches units per em:', path)
        return
    for fd in missing:
        fd.FontMatrix = expected

    mode = stat.S_IMODE(path.stat().st_mode)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.otf', delete=False) as tmp:
            temporary = Path(tmp.name)
        font.save(temporary)
        font.close()
        # Check the actual serialized dictionaries before replacing the original.
        with TTFont(temporary, recalcTimestamp=False) as saved:
            saved_fds = saved['CFF '].cff.topDictIndex[0].FDArray
            if not all(matches(fd.rawDict.get('FontMatrix', []), expected) for fd in saved_fds):
                raise RuntimeError('Saved CFF FontMatrix did not verify')
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print('Restored CFF FontMatrix for %d units per em: %s' % (round(1 / scale), path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('font', type=Path)
    args = parser.parse_args()
    fix_font(args.font)


if __name__ == '__main__':
    main()
