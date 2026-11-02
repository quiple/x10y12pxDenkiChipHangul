#!/usr/bin/env python3
"""Port an upstream .glyphs source with the Glyphs 4 native framework.

Run with Glyphs 4's bundled Python; see documentation/upstream-port.md.
Writes a new candidate file and verifies it by reopening it in Glyphs 4.
"""
import argparse
from collections import defaultdict
from pathlib import Path

from Foundation import NSBundle, NSURL
import objc

APP = Path('/Applications/Glyphs 4.app')


def load_glyphs4():
    app = NSBundle.bundleWithPath_(str(APP))
    version = str(app.objectForInfoDictionaryKey_('CFBundleShortVersionString')) if app else ''
    if not version.startswith('4.'):
        raise RuntimeError('Glyphs 4 not found at %s (version %s)' % (APP, version))
    for name in ('GlyphsCore', 'GlyphsKit', 'GlyphsApp'):
        bundle = NSBundle.bundleWithPath_(str(APP / 'Contents/Frameworks' / (name + '.framework')))
        if not bundle or not bundle.load():
            raise RuntimeError('Could not load Glyphs 4 framework: ' + name)
    return objc.lookUpClass('GSFont')


def open_font(font_class, path):
    font, error = font_class.alloc().initWithURL_error_(NSURL.fileURLWithPath_(str(path)), None)
    if font is None:
        raise RuntimeError('Cannot open %s: %s' % (path, error))
    return font


def snapshot(item):
    if item is None:
        return None
    data, error = item.propertyListValueFormat_error_(3, None)
    if data is None:
        raise RuntimeError('Cannot serialize item: %s' % error)
    result = dict(data)
    result.pop('lastChange', None)
    return result


def indexed(items, key):
    result = {}
    for item in items:
        name = str(getattr(item, key)())
        if name in result:
            raise ValueError('Duplicate item: ' + name)
        result[name] = item
    return result


def includes_upstream_code(upstream, candidate):
    """Keep local additions only when all original code lines remain in order."""
    source, result = snapshot(upstream), snapshot(candidate)
    source_code, result_code = str(source.pop('code', '')), str(result.pop('code', ''))
    if source != result:
        return False
    lines = iter(line.strip() for line in result_code.splitlines() if line.strip())
    return all(any(line == wanted for line in lines)
               for wanted in (line.strip() for line in source_code.splitlines() if line.strip()))


def plan_layout(old, new, local, collection, key):
    old_items = indexed(getattr(old, collection)(), key)
    new_items = indexed(getattr(new, collection)(), key)
    local_items = indexed(getattr(local, collection)(), key)
    actions, conflicts = [], []
    for name, item in new_items.items():
        before, target = old_items.get(name), local_items.get(name)
        source_data, before_data, target_data = snapshot(item), snapshot(before), snapshot(target)
        if target is None:
            actions.append(('add', name, item))
        elif source_data == target_data:
            continue
        elif before is not None and target_data == before_data:
            actions.append(('replace', name, item))
        elif includes_upstream_code(item, target):
            continue
        else:
            conflicts.append('%s: %s' % (collection, name))
    return actions, conflicts, sorted(set(old_items) - set(new_items))


def verify_unicode(glyphs):
    owners = defaultdict(set)
    for glyph in glyphs:
        codes = glyph.unicodes()
        if codes:
            for code in codes.array():
                owners[str(code).upper()].add(str(glyph.name()))
    duplicates = {code: names for code, names in owners.items() if len(names) > 1}
    if duplicates:
        raise ValueError('Unicode conflicts: ' + repr(duplicates))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--upstream', required=True, type=Path)
    parser.add_argument('--target', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    inputs = [args.baseline, args.upstream, args.target]
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(path)
    if args.output.exists() or args.output.suffix != '.glyphs' or args.output.resolve() in [p.resolve() for p in inputs]:
        raise ValueError('Output must be a new, distinct .glyphs file')
    font_class = load_glyphs4()
    old, upstream, target = [open_font(font_class, path) for path in inputs]
    if len({font.unitsPerEm() for font in (old, upstream, target)}) != 1:
        raise ValueError('Units per em differ')
    masters = [tuple(str(m.id()) for m in f.fontMasters()) for f in (old, upstream, target)]
    if len(set(masters)) != 1:
        raise ValueError('Master IDs or order differ')
    if any(any(bool(getattr(font, direction)()) for direction in ('kerningLTR', 'kerningRTL', 'kerningVertical')) for font in (old, upstream, target)):
        raise ValueError('Kerning requires manual migration')

    old_glyphs = indexed(old.glyphs(), 'name')
    source_glyphs = indexed(upstream.glyphs(), 'name')
    local_glyphs = indexed(target.glyphs(), 'name')
    removed = sorted(set(old_glyphs) - set(source_glyphs))
    if removed:
        print('Removed upstream; retained locally:', ', '.join(removed))
    glyph_add = [n for n in source_glyphs if n not in local_glyphs]
    glyph_replace = [n for n in source_glyphs if n in local_glyphs and snapshot(source_glyphs[n]) != snapshot(local_glyphs[n])]
    verify_unicode(list(source_glyphs.values()) + [g for n, g in local_glyphs.items() if n not in source_glyphs])

    layouts = [('classes', 'name'), ('featurePrefixes', 'name'), ('features', 'tag')]
    plans, conflicts, expected_layout = {}, [], {}
    for collection, key in layouts:
        actions, errors, removed_layout = plan_layout(old, upstream, target, collection, key)
        plans[collection] = actions
        expected_layout[collection] = {name: snapshot(item) for name, item in indexed(getattr(target, collection)(), key).items()}
        for action, name, item in actions:
            expected_layout[collection][name] = snapshot(item)
        conflicts.extend(errors)
        if removed_layout:
            print('Removed upstream %s; retained locally: %s' % (collection, ', '.join(removed_layout)))
    if conflicts:
        raise ValueError('Layout conflicts require review; no output written:\n' + '\n'.join(conflicts))

    for name in glyph_replace:
        previous = local_glyphs[name]
        copied = source_glyphs[name].copy()
        copied.setId_(previous.id())
        target.removeGlyph_(previous)
        target.addGlyph_(copied)
    for name in glyph_add:
        target.addGlyph_(source_glyphs[name].copy())
    methods = {
        'classes': ('addClass_', 'replaceObjectInClassesAtIndex_withObject_'),
        'featurePrefixes': ('addFeaturePrefix_', 'replaceObjectInFeaturePrefixesAtIndex_withObject_'),
        'features': ('addFeature_', 'replaceObjectInFeaturesAtIndex_withObject_'),
    }
    # Replacements were appended by the native mutation API; restore the
    # existing order and append new upstream glyphs in upstream order.
    ordered_names = list(local_glyphs) + glyph_add
    target.setGlyphs_([target.glyphForName_(name) for name in ordered_names])
    for collection, key in layouts:
        add_method, replace_method = methods[collection]
        for action, name, item in plans[collection]:
            if action == 'add':
                getattr(target, add_method)(item.copy())
            else:
                index = next(i for i, existing in enumerate(getattr(target, collection)()) if str(getattr(existing, key)()) == name)
                getattr(target, replace_method)(index, item.copy())
    result, error = target.saveToURL_type_format_error_(NSURL.fileURLWithPath_(str(args.output)), 1, 3, None)
    if not result:
        raise RuntimeError('Save failed: %s' % error)

    # Check the serialized candidate rather than trusting only in-memory copies.
    saved = open_font(font_class, args.output)
    saved_glyphs = indexed(saved.glyphs(), 'name')
    differences = [name for name, glyph in source_glyphs.items() if name not in saved_glyphs or snapshot(glyph) != snapshot(saved_glyphs[name])]
    local_only = set(local_glyphs) - set(source_glyphs)
    differences.extend(name for name in local_only if name not in saved_glyphs or snapshot(local_glyphs[name]) != snapshot(saved_glyphs[name]))
    if list(saved_glyphs) != ordered_names:
        differences.append('glyph order')
    for collection, key in layouts:
        actual = indexed(getattr(saved, collection)(), key)
        for name, expected in expected_layout[collection].items():
            if name not in actual or snapshot(actual[name]) != expected:
                differences.append(collection + ' local: ' + name)
        for name, item in indexed(getattr(upstream, collection)(), key).items():
            if name not in actual or not (snapshot(item) == snapshot(actual[name]) or includes_upstream_code(item, actual[name])):
                differences.append(collection + ': ' + name)
    if differences:
        args.output.unlink(missing_ok=True)
        raise RuntimeError('Saved candidate did not verify: ' + ', '.join(differences))
    print('Glyphs added: %d; replaced: %d; local-only preserved: %d' % (len(glyph_add), len(glyph_replace), len(local_only)))
    print('Layout changes:', {kind: len(actions) for kind, actions in plans.items()})
    print('Verified candidate:', args.output)


if __name__ == '__main__':
    main()
